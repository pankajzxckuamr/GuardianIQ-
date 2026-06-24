from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.authorization.schemas import AuthorizationRequest
from app.modules.authorization.decision_service import AuthorizationDecisionService
from app.shared.response_utils import ResponseHelper
from uuid import uuid4

router = APIRouter()

@router.post("/api/v1/authorization/evaluate", summary="Evaluate Authorization Decision")
async def evaluate_authorization(
    request: Request,
    payload: AuthorizationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("EVALUATE_AUTHORIZATION"))
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    
    # Auto-resolve subject_user_id if omitted for USER subjects
    if payload.subject_type == "USER" and not payload.subject_user_id:
        from app.modules.registry.repositories import resolve_user_uuid
        payload.subject_user_id = resolve_user_uuid(db, current_user.id)
    
    # We evaluate and persist the decision to the database
    service = AuthorizationDecisionService()
    response = await service.evaluate(payload, db, persist=True)
    
    return ResponseHelper.success(
        data=response.model_dump(),
        message="Authorization evaluated successfully",
        request_id=request_id
    )
