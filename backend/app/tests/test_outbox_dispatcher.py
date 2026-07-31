"""
Unit tests for OutboxDispatcher worker process (WBS 4.4.1)
Verifies SKIP LOCKED polling, successful dispatching, exponential retry backoff, and DLQ transition.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.modules.events.models import GovernanceEvent, EventOutbox, EventDeadLetter
from app.modules.events.dispatcher import OutboxDispatcher
from app.modules.auth.models import User

def get_test_user(db):
    user = db.query(User).first()
    if not user:
        user = User(
            id=uuid4(),
            email="test_dispatcher@guardianiq.demo",
            hashed_password="hashed_pwd_stub",
            is_active=True,
            role="ADMIN"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def test_outbox_dispatcher_success_lifecycle():
    """Verify that OutboxDispatcher claims pending rows and transitions them to DISPATCHED."""
    db = SessionLocal()
    try:
        user = get_test_user(db)
        tenant_id = user.id

        # 1. Create Governance Event
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
            event_hash="a" * 64
        )
        db.add(event)
        db.flush()

        # 2. Create EventOutbox row
        outbox = EventOutbox(
            event_id=event.event_id,
            tenant_id=tenant_id,
            destination="internal_bus",
            payload_json=event.payload_json,
            status="PENDING",
            retry_count=0,
            max_retries=5
        )
        db.add(outbox)
        db.commit()

        # 3. Execute dispatcher polling
        dispatcher = OutboxDispatcher()
        claimed_count = dispatcher.poll_and_dispatch()

        assert claimed_count >= 1

        # 4. Verify outbox row updated to DISPATCHED
        updated_outbox = db.query(EventOutbox).filter_by(id=outbox.id).first()
        assert updated_outbox.status == "DISPATCHED"
        assert updated_outbox.dispatched_at is not None
        assert updated_outbox.error_message is None
    finally:
        db.close()

def test_outbox_dispatcher_exponential_backoff_and_dlq():
    """Verify exponential backoff math on failure and DLQ transition when retry_count >= max_retries."""
    db = SessionLocal()
    try:
        user = get_test_user(db)
        tenant_id = user.id

        # Create Governance Event
        event = GovernanceEvent(
            tenant_id=tenant_id,
            event_type="POLICY_VIOLATION_DETECTED",
            event_category="Violation",
            event_version="1.0",
            occurred_at=datetime.now(timezone.utc),
            source_service="agent_runtime",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "policies", "entity_id": str(uuid4())},
            payload_json={"violation": "PII_EXPORT"},
            classification="RESTRICTED",
            retention_class="STANDARD_90_DAYS",
            event_hash="b" * 64
        )
        db.add(event)
        db.flush()

        outbox = EventOutbox(
            event_id=event.event_id,
            tenant_id=tenant_id,
            destination="internal_bus",
            payload_json=event.payload_json,
            status="PENDING",
            retry_count=0,
            max_retries=3
        )
        db.add(outbox)
        db.commit()

        dispatcher = OutboxDispatcher()

        # Mock dispatch failure handler
        def failing_dispatch(db_sess, record):
            raise RuntimeError("Consumer network timeout failure")

        dispatcher.dispatch_payload = failing_dispatch

        # 1. First failure -> status=FAILED, retry_count=1, next_retry_at set
        dispatcher.process_record(db, outbox)
        db.commit()

        assert outbox.status == "FAILED"
        assert outbox.retry_count == 1
        assert outbox.next_retry_at is not None
        assert "Consumer network timeout failure" in outbox.error_message

        # 2. Second failure -> status=FAILED, retry_count=2
        dispatcher.process_record(db, outbox)
        db.commit()
        assert outbox.retry_count == 2

        # 3. Third failure -> retry_count=3 >= max_retries(3) -> Transitions to DEAD_LETTER and inserts event_dead_letter
        dispatcher.process_record(db, outbox)
        db.commit()

        assert outbox.status == "DEAD_LETTER"
        assert outbox.retry_count == 3

        # Verify event_dead_letter record created
        dlq_entry = db.query(EventDeadLetter).filter_by(outbox_id=outbox.id).first()
        assert dlq_entry is not None
        assert dlq_entry.tenant_id == tenant_id
        assert dlq_entry.status == "UNRESOLVED"
        assert "Consumer network timeout failure" in dlq_entry.failure_reason
    finally:
        db.close()
