"""
E2E Integration Test Suite for Dead Letter Queue & Retry Flow (WBS 4.6.3 / QA4-006)
Tests consumer failure, exponential backoff retries, DLQ threshold transition,
API retrieval for DeadLetterReviewPage UI, and audited manual retry re-queuing.
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventOutbox, EventDeadLetter, EventSchemaRegistry, EventRetentionRule
from app.modules.events.service import EventPublisherService
from app.modules.events.dispatcher import OutboxDispatcher
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
        email=f"dlq_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="DLQ Test User",
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


def test_e2e_dead_letter_failure_dlq_transition_and_audited_retry_flow(db_session, test_user):
    """
    QA4-006: Consumer failure -> retries tracked -> DLQ transition after max retries ->
    GET /api/v1/events/dead-letter list -> POST /api/v1/events/dead-letter/{id}/retry re-queues & emits audit event.
    """
    publisher = EventPublisherService()
    now = datetime.now(timezone.utc)

    # 1. Seed schema & retention
    for etype in ["POLICY_VIOLATION_DETECTED", "DEAD_LETTER_EVENT_RETRIED"]:
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

    for cat in ["Violation", "Audit"]:
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

    # 2. Publish governance event (creates outbox entry status PENDING)
    event = publisher.publish_event(
        db_session,
        GovernanceEventCreate(
            event_type="POLICY_VIOLATION_DETECTED",
            event_category="Violation",
            event_version="1.0",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(test_user.id)},
            subject_json={"entity_type": "policies", "entity_id": "pol_999"},
            payload_json={"rule": "PII_PREVENTION"},
            classification="RESTRICTED",
            retention_class="STANDARD_90_DAYS"
        ),
        tenant_id=test_user.id
    )

    outbox_entry = db_session.query(EventOutbox).filter_by(event_id=event.event_id).first()
    assert outbox_entry is not None
    assert outbox_entry.status == "PENDING"
    assert outbox_entry.retry_count == 0

    # 3. Simulate consumer failure across max retries = 5
    dispatcher = OutboxDispatcher()
    with patch.object(OutboxDispatcher, "dispatch_payload", side_effect=RuntimeError("Simulated Consumer Failure")):
        for attempt in range(5):
            db_session.refresh(outbox_entry)
            outbox_entry.next_retry_at = None # Force ready
            db_session.commit()
            dispatcher.poll_and_dispatch()

    # Verify outbox entry transitioned to DEAD_LETTER
    db_session.expire_all()
    outbox_entry = db_session.query(EventOutbox).filter_by(event_id=event.event_id).first()
    assert outbox_entry.status == "DEAD_LETTER"
    assert outbox_entry.retry_count == 5

    # Verify event_dead_letter record created with status UNRESOLVED
    dlq_record = db_session.query(EventDeadLetter).filter_by(outbox_id=outbox_entry.id).first()
    assert dlq_record is not None
    assert dlq_record.status == "UNRESOLVED"
    assert "Simulated Consumer Failure" in dlq_record.failure_reason

    # 4. Verify GET /api/v1/events/dead-letter returns item for UI
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    client = TestClient(app)

    list_res = client.get("/api/v1/events/dead-letter")
    assert list_res.status_code == 200
    list_body = list_res.json()
    assert list_body["status"] == "success"
    dlq_items = list_body["data"]["dead_letters"]

    matching_dlq = [item for item in dlq_items if item["id"] == str(dlq_record.id)]
    assert len(matching_dlq) == 1
    assert matching_dlq[0]["status"] == "UNRESOLVED"

    # 5. Call POST /api/v1/events/dead-letter/{id}/retry (Simulate UI action click)
    retry_res = client.post(f"/api/v1/events/dead-letter/{dlq_record.id}/retry")
    assert retry_res.status_code == 200
    retry_body = retry_res.json()
    assert retry_body["status"] == "success"
    assert retry_body["data"]["status"] == "RESOLVED"

    # Verify Outbox re-queued to PENDING with retry_count = 0
    db_session.expire_all()
    updated_outbox = db_session.query(EventOutbox).filter_by(id=outbox_entry.id).first()
    assert updated_outbox.status == "PENDING"
    assert updated_outbox.retry_count == 0

    # Verify Dead Letter record updated to RESOLVED
    updated_dlq = db_session.query(EventDeadLetter).filter_by(id=dlq_record.id).first()
    assert updated_dlq.status == "RESOLVED"
    assert updated_dlq.resolved_by == test_user.id

    # Verify DEAD_LETTER_EVENT_RETRIED audit governance event emitted
    retry_audit_event = db_session.query(GovernanceEvent).filter(
        GovernanceEvent.tenant_id == test_user.id,
        GovernanceEvent.event_type == "DEAD_LETTER_EVENT_RETRIED"
    ).order_by(GovernanceEvent.occurred_at.desc()).first()

    assert retry_audit_event is not None
    assert retry_audit_event.subject_json["entity_id"] == str(dlq_record.id)
    assert retry_audit_event.payload_json["original_event_id"] == str(event.event_id)

    app.dependency_overrides.clear()
