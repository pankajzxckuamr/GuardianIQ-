from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.audit.schemas import AuditEventCreate, AuditEventResponse
from app.modules.audit.service import create_audit_event, get_audit_events
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"]
)


@router.post(
    "",
    response_model=StandardResponse[AuditEventResponse]
)
def create_audit_event_api(
    payload: AuditEventCreate,
    db: Session = Depends(get_db)
):
    result = create_audit_event(db, payload)
    return ResponseHelper.created(
        data=result,
        message="Audit event created successfully"
    )


@router.get(
    "",
    response_model=StandardResponse[list[AuditEventResponse]]
)
def get_audit_events_api(
    db: Session = Depends(get_db)
):
    result = get_audit_events(db)
    return ResponseHelper.list_response(
        items=result,
        message="Audit events retrieved successfully"
    )
