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

    audit_event = RegistryAuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        changed_by=changed_by,
        change_summary=change_summary,
        before_json=sanitize(before_json),
        after_json=sanitize(after_json)
    )
    
    db.add(audit_event)
    # Note: We do NOT commit here. This should be committed by the caller in the same transaction.
