from sqlalchemy.orm import Session
from app.modules.policy.models import Policy
from app.modules.policy.schemas import PolicyCreate


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
