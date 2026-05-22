from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.policy.schemas import PolicyCreate, PolicyResponse
from app.modules.policy.service import create_policy, get_policies


router = APIRouter(
    prefix="/api/policies",
    tags=["Policies"]
)


@router.post(
    "",
    response_model=PolicyResponse
)
def create_policy_api(
    payload: PolicyCreate,
    db: Session = Depends(get_db)
):
    return create_policy(db, payload)


@router.get(
    "",
    response_model=list[PolicyResponse]
)
def get_policies_api(
    db: Session = Depends(get_db)
):
    return get_policies(db)
