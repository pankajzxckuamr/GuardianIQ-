from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.registry.models import RegistryAuditEvent

def write_registry_audit(
    db: Session,
    entity_type: str,
    entity_id: UUID,
    event_type: str,
    changed_by: Optional[UUID],
    before_json: Optional[dict] = None,
    after_json: Optional[dict] = None,
    change_summary: Optional[str] = None
):
    # Sanitize JSON payloads (don't include sensitive info like passwords, tokens)
    # Since registry entities don't have passwords, simple copy is fine, but
    # we enforce the rule structurally.
    
    def sanitize(payload):
        if not payload:
            return None
        sanitized = payload.copy()
        for key in ['password', 'token', 'secret', 'client_secret']:
            if key in sanitized:
                sanitized[key] = '***'
        return sanitized

    from app.modules.registry.repositories import resolve_user_uuid
    changed_by = resolve_user_uuid(db, changed_by)

    meta = {
        "change_summary": change_summary,
        "before_json": sanitize(before_json),
        "after_json": sanitize(after_json)
    }

    audit_event = RegistryAuditEvent(
        event_type=f"{entity_type}_{event_type}".upper(),
        entity_type=entity_type.lower(),
        entity_id=entity_id,
        actor_user_id=changed_by,
        action=event_type,
        event_metadata=meta
    )
    
    db.add(audit_event)

    try:
        from app.modules.events.service import EventPublisherService
        from app.modules.events.schemas import GovernanceEventCreate
        from datetime import datetime, timezone
        
        publisher = EventPublisherService()
        if changed_by:
            gov_event = GovernanceEventCreate(
                event_type=f"{entity_type}_{event_type}".upper(),
                event_category="Registry",
                event_version="1.0",
                occurred_at=datetime.now(timezone.utc),
                source_service="registry_service",
                actor_json={"user_id": str(changed_by)},
                subject_json={"entity_type": entity_type, "entity_id": str(entity_id)},
                payload_json=meta,
                classification="INTERNAL",
                retention_class="STANDARD_90_DAYS"
            )
            publisher.publish_event(db, gov_event, changed_by)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to publish Phase 4 Governance event from registry: {e}")

    # Note: We do NOT commit here. This should be committed by the caller in the same transaction.
