from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.policy.schemas import PolicyCreate, PolicyResponse
from app.modules.policy.service import create_policy, get_policies
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse
from app.modules.audit.service import create_audit_event
from app.modules.audit.schemas import AuditEventCreate


router = APIRouter(
    prefix="/api/policies",
    tags=["Policies"]
)


@router.post(
    "",
    response_model=StandardResponse[PolicyResponse]
)
def create_policy_api(
    request: Request,
    payload: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = create_policy(db, payload)
    
    # Wire audit event logging
    create_audit_event(
        db,
        AuditEventCreate(
            event_type="POLICY_CREATED",
            entity_type="POLICY",
            entity_id=result.id,
            actor_user_id=current_user.id,
            action="CREATE",
            event_metadata={
                "policy_name": result.policy_name,
                "risk_level": result.severity,
                "ip_address": request.client.host if request.client else "127.0.0.1",
                "user_agent": request.headers.get("user-agent") or "Unknown",
                "status": "success",
                "detail": f"Action CREATE on POLICY"
            }
        )
    )
    
    return ResponseHelper.created(
        data=result,
        message="Policy created successfully"
    )


@router.get(
    "",
    response_model=StandardResponse[list[PolicyResponse]]
)
def get_policies_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = get_policies(db)
    return ResponseHelper.list_response(
        items=result,
        message="Policies retrieved successfully"
    )
