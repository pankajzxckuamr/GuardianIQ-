import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.policy.models import Policy
from app.modules.policy.schemas import PolicyCreate
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate

publisher_service = EventPublisherService()


def create_policy(
    db: Session,
    payload: PolicyCreate
):
    policy = Policy(
        policy_name=payload.policy_name,
        policy_type=payload.policy_type,
        severity=payload.severity.value,
        status=payload.status.value,
        conditions=payload.conditions,
        actions=payload.actions,
        created_by=payload.created_by
    )

    db.add(policy)

    db.commit()

    db.refresh(policy)

    return policy


def get_policies(db: Session):
    return db.query(Policy).all()


def trigger_policy(
    db: Session,
    policy_id: uuid.UUID,
    tenant_id: uuid.UUID,
    trigger_context: Optional[Dict[str, Any]] = None,
    actor_id: Optional[uuid.UUID] = None
):
    """
    Triggers a policy evaluation/action and emits a POLICY_TRIGGERED governance event.
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    now = datetime.now(timezone.utc)

    event_data = GovernanceEventCreate(
        event_type="POLICY_TRIGGERED",
        event_category="Policy",
        event_version="1.0",
        occurred_at=now,
        source_service="policy_engine",
        actor_json={"user_id": str(actor_id or tenant_id)},
        subject_json={
            "entity_type": "policies",
            "entity_id": str(policy_id),
            "entity_code": policy.policy_name if policy else "UNKNOWN"
        },
        payload_json=trigger_context or {},
        classification="CONFIDENTIAL",
        retention_class="STANDARD_90_DAYS"
    )

    publisher_service.publish_event(db, event_data, tenant_id)
    return policy

