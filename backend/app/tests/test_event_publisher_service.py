"""
Unit tests for EventPublisherService (WBS 4.3.3)
Verifies transactional outbox pattern, actor enrichment, SHA-256 hashing, and correlation ID handling.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.modules.events.models import GovernanceEvent, EventOutbox
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.auth.models import User

def get_or_create_test_user(db):
    user = db.query(User).first()
    if not user:
        user = User(
            id=uuid4(),
            email="test_publisher@guardianiq.demo",
            hashed_password="hashed_pwd_stub",
            is_active=True,
            role="ADMIN"
        )
        db.add(user)
        db.flush()
    return user

def test_publish_event_transactional_outbox_atomicity():
    """Verify event creation and outbox row generation commit together in same transaction."""
    db = SessionLocal()
    try:
        user = get_or_create_test_user(db)
        tenant_id = user.id

        publisher = EventPublisherService()

        event_in = GovernanceEventCreate(
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id), "roles": ["ADMIN"]},
            subject_json={"entity_type": "workflows", "entity_id": str(uuid4())},
            payload_json={"run_mode": "AUTOMATED", "parameters": {"step": 1}}
        )

        published_event = publisher.publish_event(db, event_in, tenant_id)
        db.commit()

        # Verify governance_events persistence
        db_event = db.query(GovernanceEvent).filter_by(event_id=published_event.event_id).first()
        assert db_event is not None
        assert db_event.tenant_id == tenant_id
        assert db_event.event_type == "WORKFLOW_RUN_STARTED"
        assert len(db_event.event_hash) == 64

        # Verify transactional outbox row creation
        outbox_row = db.query(EventOutbox).filter_by(event_id=published_event.event_id).first()
        assert outbox_row is not None
        assert outbox_row.tenant_id == tenant_id
        assert outbox_row.status == "PENDING"
        assert outbox_row.retry_count == 0
    finally:
        db.close()

def test_enrich_event_correlation_and_causation_handling():
    """Verify business correlation ID auto-generation and causation ID preservation."""
    db = SessionLocal()
    try:
        user = get_or_create_test_user(db)
        tenant_id = user.id
        publisher = EventPublisherService()

        # 1. Unsupplied correlation_id -> Auto-generate business correlation_id
        event1_in = GovernanceEventCreate(
            event_type="AGENT.STEP_STARTED",
            event_category="Agent",
            occurred_at=datetime.now(timezone.utc),
            source_service="agent_runtime",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "agents", "entity_id": str(uuid4())},
            payload_json={"step_no": 1}
        )
        enriched1 = publisher.enrich_event(event1_in, tenant_id)
        assert enriched1["correlation_id"] is not None
        assert enriched1["causation_id"] is None

        # 2. Supplied correlation_id & causation_id -> Preserve values
        parent_event_id = uuid4()
        custom_correlation_id = uuid4()
        event2_in = GovernanceEventCreate(
            event_type="AGENT.STEP_COMPLETED",
            event_category="Agent",
            occurred_at=datetime.now(timezone.utc),
            source_service="agent_runtime",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "agents", "entity_id": str(uuid4())},
            correlation_id=custom_correlation_id,
            causation_id=parent_event_id,
            payload_json={"step_no": 1, "result": "SUCCESS"}
        )
        enriched2 = publisher.enrich_event(event2_in, tenant_id)
        assert enriched2["correlation_id"] == custom_correlation_id
        assert enriched2["causation_id"] == parent_event_id
    finally:
        db.close()
