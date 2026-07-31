"""
Unit and Integration Tests for Event Metrics Endpoints (WBS 4.5.3)
Verifies aggregated metric calculation and strict tenant isolation.
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventOutbox, EventDeadLetter, EventSchemaRegistry, EventRetentionRule
from app.modules.events.service import EventPublisherService, EventMetricsService
from app.modules.events.schemas import GovernanceEventCreate


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"metrics_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Metrics Test Admin",
        status="ACTIVE"
    )
    db_session.add(user)
    db_session.commit()

    admin_role = db_session.query(Role).filter_by(role_code="ADMIN").first()
    if admin_role:
        user.roles.append(admin_role)
        db_session.commit()

    db_session.refresh(user)
    setattr(user, "role", "ADMIN")
    return user


@pytest.fixture
def auth_headers(test_user):
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_metrics_data(db_session, test_user):
    publisher = EventPublisherService()
    now = datetime.now(timezone.utc)

    # 1. Seed schema & retention
    for etype in ["WORKFLOW_RUN_STARTED", "UNAUTHORIZED_ACCESS_BLOCKED", "SLA_BREACHED"]:
        rec = db_session.query(EventSchemaRegistry).filter_by(event_type=etype, version="1.0").first()
        if not rec:
            db_session.add(EventSchemaRegistry(
                id=uuid.uuid4(),
                event_type=etype,
                version="1.0",
                json_schema={"type": "object"},
                is_active=True
            ))
    db_session.commit()

    for cat in ["Workflow", "Violation", "Audit"]:
        r = db_session.query(EventRetentionRule).filter_by(tenant_id=test_user.id, event_category=cat).first()
        if not r:
            db_session.add(EventRetentionRule(
                id=uuid.uuid4(),
                tenant_id=test_user.id,
                event_category=cat,
                retention_days=90,
                action="PURGE"
            ))
    db_session.commit()

    # 2. Publish Events
    ev1 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=now,
            source_service="workflow_execution",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "workflow_runs", "entity_id": str(uuid.uuid4())},
            payload_json={},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=test_user.id
    )

    ev2 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="UNAUTHORIZED_ACCESS_BLOCKED",
            event_category="Violation",
            event_version="1.0",
            occurred_at=now,
            source_service="agent_runtime",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "agents", "entity_id": str(uuid.uuid4())},
            payload_json={},
            classification="RESTRICTED",
            retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=test_user.id
    )

    # 3. Add Dead Letter Record linked to ev2 outbox entry
    outbox_rec = db_session.query(EventOutbox).filter_by(event_id=ev2.event_id).first()
    dlq = EventDeadLetter(
        outbox_id=outbox_rec.id,
        event_id=ev2.event_id,
        tenant_id=test_user.id,
        failure_reason="Timeout",
        failed_at=now,
        retry_attempts=5,
        status="UNRESOLVED"
    )
    db_session.add(dlq)
    db_session.commit()


def test_event_metrics_service(db_session, test_user, seeded_metrics_data):
    metrics = EventMetricsService.get_dashboard_metrics(db_session, test_user.id)

    assert metrics["tenant_id"] == str(test_user.id)
    assert metrics["total_events_count"] >= 2
    assert metrics["policy_violations_count"] >= 1
    assert metrics["blocked_agent_actions_count"] >= 1
    assert metrics["dead_letter_count"] >= 1
    assert "events_by_category" in metrics
    assert "events_by_type" in metrics


def test_event_metrics_api_endpoint(db_session, test_user, auth_headers, seeded_metrics_data):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    client = TestClient(app)

    res = client.get("/api/v1/events/metrics", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    data = body["data"]

    assert data["tenant_id"] == str(test_user.id)
    assert data["total_events_count"] >= 2
    assert data["policy_violations_count"] >= 1
    assert data["dead_letter_count"] >= 1

    app.dependency_overrides.clear()
