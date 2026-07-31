"""
Unit & API tests for Consumer Idempotency and Dead Letter APIs (WBS 4.4.2)
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventOutbox, EventDeadLetter, EventProcessingLog
from app.modules.events.consumers import BaseEventConsumer

from types import SimpleNamespace

from sqlalchemy import text

def seed_test_schema_registry(db):
    event_types = ["WORKFLOW_RUN_STARTED", "POLICY_VIOLATION_DETECTED", "DEAD_LETTER_EVENT_RETRIED"]
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

TEST_DLQ_USER = None

def get_test_user_override():
    global TEST_DLQ_USER
    if TEST_DLQ_USER:
        return TEST_DLQ_USER
    db = SessionLocal()
    try:
        seed_test_schema_registry(db)
        user = db.query(User).filter_by(email="test_dlq@guardianiq.demo").first()
        if not user:
            user = User(
                id=uuid4(),
                email="test_dlq@guardianiq.demo",
                name="Test DLQ User",
                hashed_password="hashed_pwd_stub"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        TEST_DLQ_USER = SimpleNamespace(
            id=user.id,
            email=user.email,
            role="ADMIN",
            roles=[]
        )
        return TEST_DLQ_USER
    finally:
        db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = get_test_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_consumer_idempotency_prevents_duplicate_processing():
    """Verify that reprocessing an event records status SKIPPED without re-running handler."""
    db = SessionLocal()
    try:
        user = get_test_user_override()
        tenant_id = user.id

        event = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "workflows", "entity_id": str(uuid4())},
            payload_json={"step": 1},
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
            event_hash="c" * 64
        )
        db.add(event)
        db.commit()

        consumer = BaseEventConsumer(consumer_id="test_idempotent_consumer")
        execution_count = 0

        def sample_handler(evt):
            nonlocal execution_count
            execution_count += 1

        # First processing run -> PROCESSED
        res1 = consumer.process_event(db, event, sample_handler)
        db.commit()
        assert res1["status"] == "PROCESSED"
        assert execution_count == 1

        # Second processing run -> SKIPPED (idempotent skip)
        res2 = consumer.process_event(db, event, sample_handler)
        db.commit()
        assert res2["status"] == "SKIPPED"
        assert execution_count == 1  # Handler was NOT executed a second time!
    finally:
        db.close()

def test_dead_letter_api_list_and_retry_flow(client):
    """Test GET /api/v1/events/dead-letter and POST /api/v1/events/dead-letter/{id}/retry."""
    db = SessionLocal()
    try:
        user = get_test_user_override()
        tenant_id = user.id

        # 1. Create Event, Outbox, and Dead Letter record
        event = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="POLICY_VIOLATION_DETECTED",
            event_category="Violation",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="agent_runtime",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "policies", "entity_id": str(uuid4())},
            payload_json={"rule": "NO_PII"},
            classification="RESTRICTED",
            retention_class="STANDARD_90_DAYS",
            event_hash="d" * 64
        )
        db.add(event)
        db.flush()

        outbox = EventOutbox(
            event_id=event.event_id,
            tenant_id=tenant_id,
            destination="internal_bus",
            payload_json=event.payload_json,
            status="DEAD_LETTER",
            retry_count=5,
            max_retries=5,
            error_message="Consumer timeout after 5 retries"
        )
        db.add(outbox)
        db.flush()

        dlq = EventDeadLetter(
            outbox_id=outbox.id,
            event_id=event.event_id,
            tenant_id=tenant_id,
            failure_reason="Consumer timeout after 5 retries",
            failed_at=datetime.now(timezone.utc),
            retry_attempts=5,
            status="UNRESOLVED"
        )
        db.add(dlq)
        db.commit()

        dlq_id = str(dlq.id)

        # 2. GET /api/v1/events/dead-letter
        list_res = client.get("/api/v1/events/dead-letter")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["status"] == "success"
        assert list_data["data"]["total"] >= 1

        # 3. POST /api/v1/events/dead-letter/{id}/retry
        retry_res = client.post(f"/api/v1/events/dead-letter/{dlq_id}/retry")
        assert retry_res.status_code == 200
        retry_data = retry_res.json()
        assert retry_data["status"] == "success"
        assert retry_data["data"]["status"] == "RESOLVED"

        # Verify DB updates
        db.expire_all()
        updated_dlq = db.query(EventDeadLetter).filter_by(id=dlq.id).first()
        assert updated_dlq.status == "RESOLVED"
        assert updated_dlq.resolved_by == tenant_id

        updated_outbox = db.query(EventOutbox).filter_by(id=outbox.id).first()
        assert updated_outbox.status == "PENDING"
        assert updated_outbox.retry_count == 0

        # Verify audit governance event emitted
        audit_event = db.query(GovernanceEvent).filter(
            GovernanceEvent.event_type == "DEAD_LETTER_EVENT_RETRIED",
            GovernanceEvent.tenant_id == tenant_id
        ).order_by(GovernanceEvent.occurred_at.desc()).first()
        assert audit_event is not None
        assert audit_event.subject_json["entity_id"] == dlq_id
    finally:
        db.close()
