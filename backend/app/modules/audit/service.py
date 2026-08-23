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

    try:
        from app.modules.events.service import EventPublisherService
        from app.modules.events.schemas import GovernanceEventCreate
        from datetime import datetime, timezone
        
        publisher = EventPublisherService()
        tenant_id = payload.actor_user_id
        if tenant_id:
            gov_event = GovernanceEventCreate(
                event_type=payload.event_type.upper().replace(".", "_"),
                event_category="Audit",
                event_version="1.0",
                occurred_at=datetime.now(timezone.utc),
                source_service="audit_service",
                actor_json={"user_id": str(payload.actor_user_id) if payload.actor_user_id else "system"},
                subject_json={"entity_type": payload.entity_type, "entity_id": str(payload.entity_id) if payload.entity_id else "unknown"},
                payload_json=payload.event_metadata or {},
                classification="INTERNAL",
                retention_class="STANDARD_90_DAYS"
            )
            publisher.publish_event(db, gov_event, tenant_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish Phase 4 Governance event: {e}")

    db.commit()

    db.refresh(audit_event)

    return audit_event


def get_audit_events(db: Session):
    return db.query(AuditEvent).all()
