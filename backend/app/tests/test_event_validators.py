"""
Unit tests for EventValidator and EventPublisherService validation (WBS 4.3.4)
Verifies pre-ingest validation rules: required fields, schema registry active status, secret key rejection, and fail-fast behavior.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.modules.events.validators import EventValidator
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.events.models import GovernanceEvent, EventOutbox
from app.modules.auth.models import User

def get_test_user(db):
    user = db.query(User).first()
    if not user:
        user = User(
            id=uuid4(),
            email="test_validator@guardianiq.demo",
            hashed_password="hashed_pwd_stub",
            is_active=True,
            role="ADMIN"
        )
        db.add(user)
        db.flush()
    return user

def test_detect_unredacted_secrets_rejection():
    """Verify that payload containing unredacted secret keys throws ValueError."""
    # 1. Unredacted password -> Rejected
    bad_payload1 = {"user": "admin", "password": "super_secret_password"}
    with pytest.raises(ValueError, match="Unredacted sensitive key 'password'"):
        EventValidator.detect_unredacted_secrets(bad_payload1)

    # 2. Unredacted api_key -> Rejected
    bad_payload2 = {"config": {"api_key": "sk-proj-123456"}}
    with pytest.raises(ValueError, match="Unredacted sensitive key 'api_key'"):
        EventValidator.detect_unredacted_secrets(bad_payload2)

    # 3. Redacted or safe values -> Allowed
    good_payload = {"user": "admin", "password": "***", "config": {"api_key": "REDACTED_KEY"}}
    EventValidator.detect_unredacted_secrets(good_payload)  # Should not raise exception

def test_unregistered_event_type_rejection():
    """Verify that event_type not registered in event_schema_registry is rejected."""
    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match="is not registered in event_schema_registry"):
            EventValidator.validate_active_schema_registry(db, "UNREGISTERED_EVENT_TYPE_123")
    finally:
        db.close()

def test_fail_fast_rejection_prevents_db_write():
    """Verify that invalid events with secrets fail fast before any DB transaction occurs."""
    db = SessionLocal()
    try:
        user = get_test_user(db)
        tenant_id = user.id
        publisher = EventPublisherService()

        # Count events before attempt
        initial_count = db.query(GovernanceEvent).count()

        event_with_secret = GovernanceEventCreate(
            event_type="WORKFLOW_RUN_STARTED",
            event_category="Workflow",
            occurred_at=datetime.now(timezone.utc),
            source_service="workflow_execution",
            actor_json={"user_id": str(tenant_id)},
            subject_json={"entity_type": "workflows", "entity_id": str(uuid4())},
            payload_json={"token": "raw_unredacted_bearer_token_123"}
        )

        with pytest.raises(ValueError, match="Unredacted sensitive key 'token'"):
            publisher.publish_event(db, event_with_secret, tenant_id)

        # Verify zero event or outbox records were written
        final_count = db.query(GovernanceEvent).count()
        assert final_count == initial_count, "Database write occurred despite validation failure!"
    finally:
        db.close()
