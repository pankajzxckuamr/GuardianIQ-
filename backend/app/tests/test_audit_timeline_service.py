"""
Unit and API tests for AuditTimelineService (WBS 4.4.3)
Verifies query-time timeline reconstruction for subject entities and correlation stream traces.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent
from app.modules.audit.timeline_service import AuditTimelineService

def seed_test_schema_registry(db):
    event_types = ["WORKFLOW_RUN_STARTED", "WORKFLOW_RUN_COMPLETED", "POLICY_VIOLATION_DETECTED"]
    for et in event_types:
        existing = db.execute(
            text("SELECT 1 FROM event_schema_registry WHERE event_type = :type AND version = '1.0'"),
            {"type": et}
        ).fetchone()
        if not existing:
            db.execute(
                text("""
                    INSERT INTO event_schema_registry 
                    (id, event_type, version, json_schema, is_active, created_at) 
                    VALUES (:id, :type, '1.0', '{}', true, CURRENT_TIMESTAMP)
                """),
                {"id": str(uuid4()), "type": et}
            )
    db.commit()

def get_test_user_override():
    db = SessionLocal()
    try:
        seed_test_schema_registry(db)
        user = db.query(User).filter_by(email="test_timeline@guardianiq.demo").first()
        if not user:
            user = User(
                id=uuid4(),
                email="test_timeline@guardianiq.demo",
                name="Test Timeline User",
                hashed_password="hashed_pwd_stub"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return SimpleNamespace(
            id=user.id,
            email=user.email,
            role="ADMIN",
            roles=[]
        )
    finally:
        db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = get_test_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_subject_timeline_reconstruction():
    """Verify build_subject_timeline queries governance_events ordered by occurred_at with tenant isolation."""
    db = SessionLocal()
    try:
        user = get_test_user_override()
        tenant_id = user.id
        subject_id = str(uuid4())

        # Create two subject events
        e1 = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "workflows", "entity_id": subject_id},
            payload_json={"step": 1},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="e" * 64
        )
        e2 = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="WORKFLOW_RUN_COMPLETED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "workflows", "entity_id": subject_id},
            payload_json={"step": 2},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="f" * 64
        )
        db.add_all([e1, e2])
        db.commit()

        # Build timeline
        timeline = AuditTimelineService.build_subject_timeline(db, tenant_id, "workflows", subject_id)

        assert timeline["subject_type"] == "workflows"
        assert timeline["subject_id"] == subject_id
        assert timeline["total_events"] >= 2
        assert timeline["first_event_at"] is not None
        assert timeline["last_event_at"] is not None
        assert len(timeline["events"]) >= 2

        # Verify tenant isolation (random tenant returns 0 events)
        other_timeline = AuditTimelineService.build_subject_timeline(db, uuid4(), "workflows", subject_id)
        assert other_timeline["total_events"] == 0
    finally:
        db.close()

def test_correlation_timeline_reconstruction():
    """Verify build_correlation_timeline constructs causation chain & trace stream."""
    db = SessionLocal()
    try:
        user = get_test_user_override()
        tenant_id = user.id
        corr_id = uuid4()
        parent_evt_id = uuid4()

        e1 = GovernanceEvent(
            event_id=parent_evt_id,
            tenant_id=tenant_id,
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "workflows", "entity_id": str(uuid4())},
            correlation_id=corr_id,
            causation_id=None,
            payload_json={"step": 1},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="1" * 64
        )
        e2 = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="POLICY_VIOLATION_DETECTED",
            event_category="Violation",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="policy_engine",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "policies", "entity_id": str(uuid4())},
            correlation_id=corr_id,
            causation_id=parent_evt_id,
            payload_json={"rule": "MAX_SPEND"},
            classification="CONFIDENTIAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="2" * 64
        )
        db.add_all([e1, e2])
        db.commit()

        # Build correlation trace
        trace = AuditTimelineService.build_correlation_timeline(db, tenant_id, corr_id)

        assert trace["correlation_id"] == str(corr_id)
        assert trace["total_events"] >= 2
        assert len(trace["causation_chain"]) >= 2
        assert trace["causation_chain"][1]["causation_id"] == str(parent_evt_id)
    finally:
        db.close()

def test_subject_and_correlation_api_endpoints(client):
    """Test REST API endpoints for subject timeline and correlation trace."""
    db = SessionLocal()
    try:
        user = get_test_user_override()
        tenant_id = user.id
        subject_id = str(uuid4())
        corr_id = str(uuid4())

        e1 = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "agents", "entity_id": subject_id},
            correlation_id=corr_id,
            payload_json={"step": 1},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="3" * 64
        )
        db.add(e1)
        db.commit()

        # GET subject timeline API
        res1 = client.get(f"/api/v1/events/subject/agents/{subject_id}")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "success"
        assert data1["data"]["total_events"] >= 1

        # GET correlation trace stream API
        res2 = client.get(f"/api/v1/events/correlation/{corr_id}")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "success"
        assert data2["data"]["correlation_id"] == corr_id
    finally:
        db.close()
