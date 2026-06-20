from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa
from app.shared.db_compat import execute_statement

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.workflow_notifications.models import WorkflowNotification

router = APIRouter()

def make_envelope(success: bool, data: any, error: str | None, request_id: str) -> dict:
    return {
        "status": "success" if success else "error",
        "success": success,
        "data": data,
        "error": error,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/api/v1/workflow-notifications")
async def list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="per_page"),
    status: str | None = None,
    notification_type: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        query = sa.select(WorkflowNotification).where(
            WorkflowNotification.recipient_user_id == current_user.id,
            WorkflowNotification.is_deleted == False
        )
        
        if status:
            query = query.where(WorkflowNotification.status == status)
        if notification_type:
            query = query.where(WorkflowNotification.notification_type == notification_type)
        if severity:
            query = query.where(WorkflowNotification.severity == severity)
            
        count_stmt = sa.select(sa.func.count()).select_from(query.subquery())
        count_res = await execute_statement(db, count_stmt)
        total = count_res.scalar() or 0
        
        offset = (page - 1) * page_size
        query = query.order_by(WorkflowNotification.created_at.desc()).offset(offset).limit(page_size)
        
        res = await execute_statement(db, query)
        items = res.scalars().all()
        
        formatted_items = [
            {
                "id": str(item.id),
                "recipient_user_id": str(item.recipient_user_id),
                "notification_type": item.notification_type,
                "title": item.title,
                "message": item.message,
                "severity": item.severity,
                "entity_type": item.entity_type,
                "entity_id": str(item.entity_id) if item.entity_id else None,
                "status": item.status,
                "read_at": item.read_at.isoformat() if item.read_at else None,
                "acknowledged_at": item.acknowledged_at.isoformat() if item.acknowledged_at else None,
                "created_at": item.created_at.isoformat()
            } for item in items
        ]
        
        data = {
            "items": formatted_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return make_envelope(True, data, None, request_id)
    except Exception as e:
        return make_envelope(False, None, str(e), request_id)


@router.put("/api/v1/workflow-notifications/{id}/read")
async def mark_notification_read(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = sa.select(WorkflowNotification).where(
            WorkflowNotification.id == id,
            WorkflowNotification.recipient_user_id == current_user.id,
            WorkflowNotification.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        notif = res.scalar()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        if notif.status == 'UNREAD':
            notif.status = 'READ'
            notif.read_at = datetime.now(timezone.utc)
            db.commit()
            
        data = {
            "id": str(notif.id),
            "status": notif.status,
            "read_at": notif.read_at.isoformat() if notif.read_at else None
        }
        return make_envelope(True, data, None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)


@router.put("/api/v1/workflow-notifications/{id}/acknowledge")
async def acknowledge_notification(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    try:
        stmt = sa.select(WorkflowNotification).where(
            WorkflowNotification.id == id,
            WorkflowNotification.recipient_user_id == current_user.id,
            WorkflowNotification.is_deleted == False
        )
        res = await execute_statement(db, stmt)
        notif = res.scalar()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        if notif.status in ['UNREAD', 'READ']:
            notif.status = 'ACKNOWLEDGED'
            if not notif.read_at:
                notif.read_at = datetime.now(timezone.utc)
            notif.acknowledged_at = datetime.now(timezone.utc)
            db.commit()
            
        data = {
            "id": str(notif.id),
            "status": notif.status,
            "read_at": notif.read_at.isoformat() if notif.read_at else None,
            "acknowledged_at": notif.acknowledged_at.isoformat() if notif.acknowledged_at else None
        }
        return make_envelope(True, data, None, request_id)
    except HTTPException as e:
        db.rollback()
        return make_envelope(False, None, str(e.detail), request_id)
    except Exception as e:
        db.rollback()
        return make_envelope(False, None, str(e), request_id)
