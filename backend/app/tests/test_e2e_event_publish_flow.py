"""
E2E Integration Test Suite for Event Publish Flow (WBS 4.6.1 / QA4-001, QA4-002, QA4-003)
Tests the complete chain: Action -> Publisher -> Outbox -> Dispatcher -> Event Explorer API.
Also tests fail-closed transaction atomicity on invalid inputs.
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.modules.auth.models import User, Role
from app.modules.auth.dependencies import get_current_user
from app.modules.events.models import GovernanceEvent, EventOutbox, EventSchemaRegistry, EventRetentionRule
from app.modules.events.service import EventPublisherService
from app.modules.events.dispatcher import OutboxDispatcher
from app.modules.relationship.service import RelationshipService
from app.modules.relationship.models import GenericRelationship


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
        email=f"e2e_user_{user_id.hex[:8]}@example.com",
        hashed_password="hashed_pw",
        name="E2E Test User",
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


def test_e2e_positive_event_publishing_chain(db_session, test_user):
    """
    QA4-001 & QA4-002: Real action -> EventPublisherService -> governance_events -> event_outbox -> dispatcher -> API.
    """
    # 1. Ensure Schema Registry & Retention rule exist
    etype = "RELATIONSHIP_REVOKED"
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

    r = db_session.query(EventRetentionRule).filter_by(tenant_id=test_user.id, event_category="Relationship").first()
    if not r:
        db_session.add(EventRetentionRule(
            id=uuid.uuid4(),
            tenant_id=test_user.id,
            event_category="Relationship",
            retention_days=90,
            action="PURGE"
        ))
    db_session.commit()

    # 2. Create relationship and then revoke it (real action)
    rel_id = uuid.uuid4()
    rel = GenericRelationship(
        id=rel_id,
        tenant_id=test_user.id,
        relationship_type="USES",
        source_id="agent_alpha",
        target_id="model_beta",
        source_type="AGENT",
        target_type="MODEL",
        effective_from=datetime.now(timezone.utc),
        status="ACTIVE"
    )
    db_session.add(rel)
    db_session.commit()

    import asyncio
    rel_svc = RelationshipService(db_session, test_user.id, test_user.id)
    asyncio.run(rel_svc.revoke_relationship(rel_id, reason="Security review"))

    # 3. Verify governance_events row created atomically
    gov_event = db_session.query(GovernanceEvent).filter(
        GovernanceEvent.tenant_id == test_user.id,
        GovernanceEvent.event_type == "RELATIONSHIP_REVOKED"
    ).order_by(GovernanceEvent.occurred_at.desc()).first()

    assert gov_event is not None
    assert str(gov_event.subject_json.get("entity_id")) == str(rel_id)
    assert gov_event.event_hash is not None

    # 4. Verify event_outbox row created in the same transaction with status PENDING
    outbox_row = db_session.query(EventOutbox).filter_by(event_id=gov_event.event_id).first()
    assert outbox_row is not None
    assert outbox_row.status == "PENDING"

    # 5. Process outbox via OutboxDispatcher
    db_session.commit()
    dispatcher = OutboxDispatcher()
    processed_count = dispatcher.poll_and_dispatch()
    assert processed_count >= 1

    # Verify outbox transitions to DISPATCHED
    updated_outbox = db_session.query(EventOutbox).filter_by(event_id=gov_event.event_id).first()
    assert updated_outbox.status == "DISPATCHED"

    # 6. Verify Event Explorer API (GET /api/v1/events) retrieves the event
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    client = TestClient(app)

    res = client.get("/api/v1/events?event_type=RELATIONSHIP_REVOKED")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    events_list = body["data"]["events"]

    matching = [e for e in events_list if e["event_id"] == str(gov_event.event_id)]
    assert len(matching) == 1
    assert matching[0]["event_type"] == "RELATIONSHIP_REVOKED"

    app.dependency_overrides.clear()


def test_e2e_negative_validation_prevents_db_write(db_session, test_user):
    """
    QA4-003: Publish event missing tenant_id or subject -> API rejects with error and ZERO DB rows are created.
    """
    initial_event_count = db_session.query(GovernanceEvent).count()
    initial_outbox_count = db_session.query(EventOutbox).count()

    publisher = EventPublisherService()

    # Attempt to publish with missing tenant_id
    with pytest.raises(ValueError) as exc_info:
        publisher.publish_event(
            db_session,
            event_data=None, # Invalid
            tenant_id=None # Missing tenant_id
        )

    # Verify error details
    assert "tenant_id" in str(exc_info.value)

    # Verify direct DB counts remain completely unchanged
    new_event_count = db_session.query(GovernanceEvent).count()
    new_outbox_count = db_session.query(EventOutbox).count()

    assert new_event_count == initial_event_count
    assert new_outbox_count == initial_outbox_count
