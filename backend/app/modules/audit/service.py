from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent

from app.modules.audit.schemas import (
    AuditEventCreate
)


def create_audit_event(
    db: Session,
    payload: AuditEventCreate
):
    audit_event = AuditEvent(
        event_type=payload.event_type,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        actor_user_id=payload.actor_user_id,
        action=payload.action,
        event_metadata=payload.event_metadata
    )

    db.add(audit_event)

    db.commit()

    db.refresh(audit_event)

    return audit_event


def get_audit_events(db: Session):
    return db.query(AuditEvent).all()
