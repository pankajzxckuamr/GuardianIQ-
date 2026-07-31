"""
Unit and Integration Tests for Audit Export API & Deferred Policy/Approval Event Hooks
WBS Reference: 4.5.1
"""
import pytest
import uuid
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventExportLog, EventSchemaRegistry, EventRetentionRule
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.audit.export_service import AuditExportService
from app.modules.policy.service import trigger_policy
from app.shared.hashing import compute_sha256_hash


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
        email=f"export_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="Export Test Admin",
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
def seeded_governance_events(db_session, test_user):
    """Seed sample governance events for testing export."""
    publisher = EventPublisherService()
    now = datetime.now(timezone.utc)

    # Seed schema if missing
    for etype in ["WORKFLOW_RUN_STARTED", "POLICY_TRIGGERED", "APPROVAL_GRANTED"]:
        schema_rec = db_session.query(EventSchemaRegistry).filter_by(event_type=etype, version="1.0").first()
        if not schema_rec:
            db_session.add(EventSchemaRegistry(
                id=uuid.uuid4(),
                event_type=etype,
                version="1.0",
                json_schema={"type": "object"},
                is_active=True
            ))
    db_session.commit()

    # Seed retention rules if missing
    for cat in ["Workflow", "Policy", "Approval", "Audit"]:
        rule = db_session.query(EventRetentionRule).filter_by(tenant_id=test_user.id, event_category=cat).first()
        if not rule:
            db_session.add(EventRetentionRule(
                id=uuid.uuid4(),
                tenant_id=test_user.id,
                event_category=cat,
                retention_days=90,
                action="PURGE"
            ))
    db_session.commit()

    events = []
    # 1. Workflow run started
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
            payload_json={"mode": "AUTO"},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=test_user.id
    )
    events.append(ev1)

    # 2. Policy triggered
    ev2 = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="POLICY_TRIGGERED",
            event_category="Policy",
            event_version="1.0",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "policies", "entity_id": str(uuid.uuid4())},
            payload_json={"severity": "HIGH"},
            classification="CONFIDENTIAL",
            retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=test_user.id
    )
    events.append(ev2)

    db_session.commit()
    return events


def test_export_service_create_export(db_session, test_user, seeded_governance_events):
    export_res = AuditExportService.create_export(
        db=db_session,
        tenant_id=test_user.id,
        requested_by=test_user.id,
        filter_params={"event_category": "Workflow"},
        export_format="JSON"
    )

    assert export_res["export_id"] is not None
    assert export_res["event_count"] >= 1
    assert export_res["export_hash"] is not None
    assert len(export_res["export_hash"]) == 64  # SHA-256 hex digest

    # Verify event_export_log entry
    log_rec = db_session.query(EventExportLog).filter_by(id=uuid.UUID(export_res["export_id"])).first()
    assert log_rec is not None
    assert log_rec.tenant_id == test_user.id
    assert log_rec.exported_by == test_user.id
    assert log_rec.file_hash == export_res["export_hash"]


def test_export_api_endpoints(db_session, test_user, auth_headers, seeded_governance_events):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    client = TestClient(app)

    # 1. POST /api/v1/audit/export
    res = client.post("/api/v1/audit/export?export_format=JSON", headers=auth_headers, json={})
    assert res.status_code == 201, f"Response: {res.text}"
    body = res.json()
    assert body["status"] == "success"
    export_id = body["data"]["export_id"]
    assert export_id is not None
    assert "export_hash" in body["data"]

    # 2. GET /api/v1/audit/export/{id}
    res_status = client.get(f"/api/v1/audit/export/{export_id}", headers=auth_headers)
    assert res_status.status_code == 200, f"Status response: {res_status.text}"
    body_status = res_status.json()
    assert body_status["status"] == "success"
    assert body_status["data"]["export_id"] == export_id
    assert body_status["data"]["status"] == "COMPLETED"

    app.dependency_overrides.clear()


def test_policy_triggered_event_hook(db_session, test_user):
    policy_id = uuid.uuid4()
    trigger_policy(
        db=db_session,
        policy_id=policy_id,
        tenant_id=test_user.id,
        trigger_context={"rule": "MAX_SPEND_LIMIT_EXCEEDED"},
        actor_id=test_user.id
    )
    db_session.commit()

    ev = db_session.query(GovernanceEvent).filter(
        GovernanceEvent.tenant_id == test_user.id,
        GovernanceEvent.event_type == "POLICY_TRIGGERED"
    ).first()

    assert ev is not None
    assert str(ev.subject_json["entity_id"]) == str(policy_id)
    assert ev.payload_json["rule"] == "MAX_SPEND_LIMIT_EXCEEDED"
