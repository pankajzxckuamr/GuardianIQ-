from datetime import datetime, timezone, timedelta
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
import app.db.base
from app.modules.auth.models import User
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion, PolicyRule
from app.modules.policy_engine.service import PolicyService, PolicyVersionService
from app.modules.events.models import GovernanceEvent


def create_test_user(db: Session, email_prefix: str = "user") -> User:
    user = User(
        id=uuid4(),
        name=f"User {email_prefix}",
        full_name="Lifecycle Test User",
        email=f"{email_prefix}_{uuid4().hex[:8]}@guardianiq.ai",
        hashed_password="pw",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_policy_and_version_lifecycle_full_flow(db: Session):
    user = create_test_user(db, "lifecycle_admin")
    tenant_id = user.id
    policy_service = PolicyService(db)
    version_service = PolicyVersionService(db)
    correlation_id = uuid4()

    # 1. Create Policy in DRAFT
    pol_data = {
        "policy_code": f"POL-LC-{uuid4().hex[:6]}",
        "name": "Lifecycle Managed Policy",
        "description": "Tests full lifecycle progression",
        "category": "DATA_ACCESS",
        "enforcement_mode": "BLOCKING",
        "priority": 10,
    }
    policy = policy_service.create_policy(
        tenant_id=tenant_id,
        owner_user_id=user.id,
        policy_data=pol_data,
        correlation_id=correlation_id,
    )
    assert policy.id is not None
    assert policy.status == "DRAFT"

    # 2. Create Draft Version 1 with Rules
    rules_v1 = [
        {
            "rule_code": "RULE-LC-01",
            "name": "Mask Confidential Columns",
            "rule_type": "DATA_ACCESS",
            "target_type": "DATA_SOURCE",
            "target_id": "*",
            "action": "MODIFY",
            "severity": "HIGH",
            "execution_order": 1,
        }
    ]
    v1 = version_service.create_draft_version(
        tenant_id=tenant_id,
        policy_id=policy.id,
        user_id=user.id,
        changelog="V1 Initial Draft",
        rules_data=rules_v1,
        correlation_id=correlation_id,
    )
    assert v1.version_number == 1
    assert v1.status == "DRAFT"
    assert v1.rules_count == 1

    # 3. Activate Version 1
    v1_active = version_service.activate_version(
        tenant_id=tenant_id,
        policy_id=policy.id,
        version_id=v1.id,
        user_id=user.id,
        correlation_id=correlation_id,
    )
    assert v1_active.status == "ACTIVE"
    assert policy.status == "ACTIVE"

    # 4. Attempt to modify active Version 1 -> must fail with ValueError
    with pytest.raises(ValueError) as excinfo:
        version_service.update_draft_version(
            tenant_id=tenant_id,
            version_id=v1.id,
            changelog="Attempted Tampering",
        )
    assert "cannot modify immutable policy version" in str(excinfo.value).lower()

    # 5. Create Draft Version 2
    rules_v2 = [
        {
            "rule_code": "RULE-LC-01-EXP",
            "name": "Expanded Column Redaction",
            "rule_type": "DATA_ACCESS",
            "target_type": "DATA_SOURCE",
            "target_id": "*",
            "action": "DENY",
            "severity": "CRITICAL",
            "execution_order": 1,
        }
    ]
    v2 = version_service.create_draft_version(
        tenant_id=tenant_id,
        policy_id=policy.id,
        user_id=user.id,
        changelog="V2 Enhanced Rules",
        rules_data=rules_v2,
        correlation_id=correlation_id,
    )
    assert v2.version_number == 2
    assert v2.status == "DRAFT"

    # 6. Activate Version 2 -> V1 must be superseded
    v2_active = version_service.activate_version(
        tenant_id=tenant_id,
        policy_id=policy.id,
        version_id=v2.id,
        user_id=user.id,
        correlation_id=correlation_id,
    )
    assert v2_active.status == "ACTIVE"

    # Refresh V1 from DB
    db.refresh(v1)
    assert v1.status == "SUPERSEDED"

    # 7. Suspend Policy
    pol_suspended = policy_service.suspend_policy(
        tenant_id=tenant_id,
        policy_id=policy.id,
        user_id=user.id,
        reason="Security audit in progress",
        correlation_id=correlation_id,
    )
    assert pol_suspended.status == "SUSPENDED"

    # 8. Retire Policy
    pol_retired = policy_service.retire_policy(
        tenant_id=tenant_id,
        policy_id=policy.id,
        user_id=user.id,
        reason="Policy deprecated and replaced",
        correlation_id=correlation_id,
    )
    assert pol_retired.status == "RETIRED"
    db.refresh(v2)
    assert v2.status == "RETIRED"

    # 9. Verify Audit Events emitted into governance_events table
    events = (
        db.query(GovernanceEvent)
        .filter(
            GovernanceEvent.tenant_id == tenant_id,
            GovernanceEvent.correlation_id == correlation_id,
        )
        .order_by(GovernanceEvent.occurred_at.asc())
        .all()
    )
    assert len(events) >= 5
    event_types = [e.event_type for e in events]
    assert "POLICY_CREATED" in event_types
    assert "POLICY_VERSION_CREATED" in event_types
    assert "POLICY_VERSION_ACTIVATED" in event_types
    assert "POLICY_SUSPENDED" in event_types
    assert "POLICY_RETIRED" in event_types

    # Ensure every event has SHA-256 hash
    for e in events:
        assert e.event_hash is not None
        assert len(e.event_hash) == 64
        assert e.source_service == "policy_engine"
