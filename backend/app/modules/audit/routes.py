from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.audit.schemas import AuditEventCreate, AuditEventResponse
from app.modules.audit.service import create_audit_event, get_audit_events

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"]
)


@router.post(
    "",
    response_model=AuditEventResponse
)
def create_audit_event_api(
    payload: AuditEventCreate,
    db: Session = Depends(get_db)
):
    return create_audit_event(db, payload)


@router.get(
    "",
    response_model=list[AuditEventResponse]
)
def get_audit_events_api(
    db: Session = Depends(get_db)
):
    return get_audit_events(db)
