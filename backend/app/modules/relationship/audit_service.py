import uuid
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.modules.audit.event_service import GovernanceEventService

from datetime import datetime

def make_serializable(data):
    if isinstance(data, dict):
        return {k: make_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_serializable(v) for v in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, uuid.UUID):
        return str(data)
    return data

class RelationshipAuditService:
    def __init__(self, db: Session, current_user_id: uuid.UUID):
        self.db = db
        self.current_user_id = current_user_id
        self.audit = GovernanceEventService()

    async def _publish(self, event_code: str, entity_type: str, entity_id: uuid.UUID, action: str, summary: str, payload: dict):
        await self.audit.publish_event(
            event_code=event_code,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type="USER",
            actor_id=self.current_user_id,
            action_type=action,
            event_summary=summary,
            event_payload=make_serializable(payload),
            db=self.db
        )

    async def publish_relationship_created(self, rel_id: uuid.UUID, payload: dict):
        await self._publish("RELATIONSHIP_CREATED", "generic_relationships", rel_id, "CREATE", "Relationship created", payload)

    async def publish_relationship_updated(self, rel_id: uuid.UUID, before: dict, after: dict):
        await self._publish("RELATIONSHIP_UPDATED", "generic_relationships", rel_id, "UPDATE", "Relationship updated", {"before": before, "after": after})

    async def publish_relationship_revoked(self, rel_id: uuid.UUID, reason: str):
        await self._publish("RELATIONSHIP_REVOKED", "generic_relationships", rel_id, "REVOKE", "Relationship revoked", {"reason": reason})

    async def publish_relationship_suspended(self, rel_id: uuid.UUID, payload: dict):
        await self._publish("RELATIONSHIP_SUSPENDED", "generic_relationships", rel_id, "SUSPEND", "Relationship suspended", payload)

    async def publish_relationship_expired(self, rel_id: uuid.UUID, payload: dict):
        await self._publish("RELATIONSHIP_EXPIRED", "generic_relationships", rel_id, "EXPIRE", "Relationship expired", payload)

    async def publish_relationship_approved(self, rel_id: uuid.UUID, payload: dict):
        await self._publish("RELATIONSHIP_APPROVED", "generic_relationships", rel_id, "APPROVE", "Relationship approved", payload)

    async def publish_relationship_activated(self, rel_id: uuid.UUID, payload: dict):
        await self._publish("RELATIONSHIP_ACTIVATED", "generic_relationships", rel_id, "ACTIVATE", "Relationship activated", payload)

    async def publish_validation_failed(self, request_id: str, rule_id: str, message: str):
        await self._publish("RELATIONSHIP_VALIDATION_FAILED", "generic_relationships", None, "VALIDATE", "Validation failed", {"request_id": request_id, "rule_id": rule_id, "message": message})

    async def publish_responsibility_assigned(self, object_type: str, object_id: uuid.UUID, responsibility_type: str, previous_assignee: Optional[str] = None):
        await self._publish("RESPONSIBILITY_ASSIGNED", object_type, object_id, "ASSIGN_RESPONSIBILITY", f"Assigned {responsibility_type}", {"responsibility_type": responsibility_type, "previous_assignee": previous_assignee})

    async def publish_governance_context_built(self, object_type: str, object_id: uuid.UUID):
        await self._publish("GOVERNANCE_CONTEXT_BUILT", object_type, object_id, "READ_CONTEXT", "Governance context resolved", {})

    async def publish_graph_traversal(self, object_type: str, object_id: uuid.UUID, depth: int):
        await self._publish("GRAPH_TRAVERSAL_PERFORMED", object_type, object_id, "TRAVERSE_GRAPH", "Graph traversed", {"depth": depth})

    async def publish_impact_analysis(self, object_type: str, object_id: uuid.UUID, depth: int, change_type: str):
        await self._publish("IMPACT_ANALYSIS_PERFORMED", object_type, object_id, "IMPACT_ANALYSIS", "Impact analysis executed", {"depth": depth, "change_type": change_type})

    async def publish_audit_timeline_viewed(self, object_type: str, object_id: uuid.UUID):
        await self._publish("AUDIT_TIMELINE_VIEWED", object_type, object_id, "VIEW_TIMELINE", "Audit timeline viewed", {})

    async def get_timeline(self, entity_type: str, entity_id: uuid.UUID) -> list:
        # Calls the underlying event service
        return await self.audit.get_timeline(entity_type, entity_id, self.db)
