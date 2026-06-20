from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.audit.models import AuditEvent
from app.modules.audit.schemas import AuditEventCreate, AuditEventResponse, AuditEventPaginated
from app.modules.audit.service import create_audit_event
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = create_audit_event(db, payload)
    return ResponseHelper.created(
        data=result,
        message="Audit event created successfully"
    )


@router.get(
    "/events",
    response_model=StandardResponse[AuditEventPaginated]
)
def get_audit_events_api(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1),
    event_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    created_after: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditEvent, User.name.label("actor_username")).outerjoin(
        User, AuditEvent.actor_user_id == User.id
    )
    
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if actor_id:
        query = query.filter(AuditEvent.actor_user_id == actor_id)
    if created_after:
        query = query.filter(AuditEvent.created_at >= created_after)
        
    total = query.count()
    
    # Sort and Paginate
    offset = (page - 1) * per_page
    results = query.order_by(AuditEvent.created_at.desc()).offset(offset).limit(per_page).all()
    
    response_items = []
    for event, actor_username in results:
        meta = event.event_metadata or {}
        ip_address = meta.get("ip_address") or meta.get("ip") or "127.0.0.1"
        user_agent = meta.get("user_agent") or "Mozilla/5.0"
        status = meta.get("status") or "success"
        detail = meta.get("detail") or f"Action {event.action} on {event.entity_type}"
        
        response_items.append(
            AuditEventResponse(
                id=event.id,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=str(event.entity_id) if event.entity_id is not None else None,
                actor_user_id=event.actor_user_id,
                actor_username=actor_username or "system",
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                detail=detail,
                created_at=event.created_at
            )
        )
        
    pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    
    data = AuditEventPaginated(
        items=response_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )
    
    return ResponseHelper.success(
        data=data,
        message="Audit events retrieved successfully"
    )

