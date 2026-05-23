from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.policy.schemas import PolicyCreate, PolicyResponse
from app.modules.policy.service import create_policy, get_policies
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse


router = APIRouter(
    prefix="/api/policies",
    tags=["Policies"]
)


@router.post(
    "",
    response_model=StandardResponse[PolicyResponse]
)
def create_policy_api(
    payload: PolicyCreate,
    db: Session = Depends(get_db)
):
    result = create_policy(db, payload)
    return ResponseHelper.created(
        data=result,
        message="Policy created successfully"
    )


@router.get(
    "",
    response_model=StandardResponse[list[PolicyResponse]]
)
def get_policies_api(
    db: Session = Depends(get_db)
):
    result = get_policies(db)
    return ResponseHelper.list_response(
        items=result,
        message="Policies retrieved successfully"
    )
