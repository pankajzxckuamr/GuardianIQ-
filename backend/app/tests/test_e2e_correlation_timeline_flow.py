"""
E2E Integration Test Suite for Correlation Timeline Flow (WBS 4.6.2 / QA4-004)
Verifies multi-step correlated event flow reconstruction, chronological ordering, and API integration.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventSchemaRegistry, EventRetentionRule
from app.modules.events.service import EventPublisherService
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
        email=f"corr_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Correlation Test User",
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


def test_e2e_correlation_timeline_chain_reconstruction(db_session, test_user):
    """
    QA4-004: Multi-step event chain sharing correlation_id is returned chronologically ordered by API.
    """
    publisher = EventPublisherService()
    correlation_id = uuid.uuid4()
    base_time = datetime.now(timezone.utc) - timedelta(minutes=15)

    # 1. Seed schema & retention
    for etype in ["WORKFLOW_RUN_STARTED", "AGENT_ACTION_BLOCKED", "WORKFLOW_RUN_COMPLETED"]:
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

    for cat in ["Workflow", "Boundary"]:
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

    # Step 1: WORKFLOW_RUN_STARTED (t0)
    ev1 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=base_time,
            source_service="workflow_execution",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "workflow_runs", "entity_id": "run_1001"},
            payload_json={"step": "START"},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            correlation_id=correlation_id
        ),
        tenant_id=test_user.id
    )

    # Step 2: AGENT_ACTION_BLOCKED (t0 + 5m, parent = ev1)
    ev2 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="AGENT_ACTION_BLOCKED",
            event_category="Boundary",
            event_version="1.0",
            occurred_at=base_time + timedelta(minutes=5),
            source_service="agent_runtime",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "agents", "entity_id": "agent_safety_bot"},
            payload_json={"reason": "Write tool prohibited in READ_ONLY mode"},
            classification="RESTRICTED",
            retention_class="STANDARD_90_DAYS",
            correlation_id=correlation_id,
            parent_event_id=ev1.event_id,
            causation_id=ev1.event_id
        ),
        tenant_id=test_user.id
    )

    # Step 3: WORKFLOW_RUN_COMPLETED (t0 + 10m, parent = ev2)
    ev3 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="WORKFLOW_RUN_COMPLETED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=base_time + timedelta(minutes=10),
            source_service="workflow_execution",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "workflow_runs", "entity_id": "run_1001"},
            payload_json={"status": "COMPLETED_WITH_WARNINGS"},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            correlation_id=correlation_id,
            parent_event_id=ev2.event_id,
            causation_id=ev2.event_id
        ),
        tenant_id=test_user.id
    )

    db_session.commit()

    # 2. Verify all 3 events share the exact same correlation_id in database
    correlated_db_rows = db_session.query(GovernanceEvent).filter(
        GovernanceEvent.tenant_id == test_user.id,
        GovernanceEvent.correlation_id == correlation_id
    ).all()

    assert len(correlated_db_rows) == 3

    # 3. Test API Endpoint GET /api/v1/events/correlation/{correlation_id}
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    client = TestClient(app)

    res = client.get(f"/api/v1/events/correlation/{correlation_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["correlation_id"] == str(correlation_id)
    assert data["total_events"] == 3

    events = data["events"]
    assert len(events) == 3

    # Verify chronological ordering (occurred_at ascending)
    assert events[0]["event_type"] == "WORKFLOW_RUN_STARTED"
    assert events[1]["event_type"] == "AGENT_ACTION_BLOCKED"
    assert events[2]["event_type"] == "WORKFLOW_RUN_COMPLETED"

    # Verify causation event linkage
    assert events[1]["causation_id"] == str(ev1.event_id)
    assert events[2]["causation_id"] == str(ev2.event_id)

    # Verify causation chain in response
    causation_chain = data["causation_chain"]
    assert len(causation_chain) == 3
    assert causation_chain[1]["causation_id"] == str(ev1.event_id)

    app.dependency_overrides.clear()
