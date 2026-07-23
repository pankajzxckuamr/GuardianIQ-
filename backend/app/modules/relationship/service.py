import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.modules.relationship.models import GenericRelationship
from app.modules.relationship.schemas import GenericRelationshipCreate, GenericRelationshipUpdate
from app.modules.relationship.repository import RelationshipRepository
from app.modules.relationship.validators import ValidationEngine
from app.modules.relationship.audit_service import RelationshipAuditService
from app.modules.relationship.constants import LifecycleState

class RelationshipService:
    def __init__(self, db: Session, tenant_id: uuid.UUID, current_user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.repo = RelationshipRepository()
        self.validator = ValidationEngine(db, tenant_id)
        self.audit = RelationshipAuditService(db, current_user_id)

    async def create_relationship(self, request_id: str, payload: GenericRelationshipCreate) -> Tuple[Optional[GenericRelationship], List[dict]]:
        # Validate payload
        validation_results = self.validator.validate_payload(request_id, payload.model_dump())
        has_errors = any(r.status == "FAIL" and r.severity == "ERROR" for r in validation_results)
        if has_errors:
            for r in validation_results:
                if r.status == "FAIL":
                    await self.audit.publish_validation_failed(request_id, r.rule_id, r.message)
            return None, [{"rule_id": r.rule_id, "message": r.message} for r in validation_results if r.status == "FAIL"]

        # Create
        new_rel = GenericRelationship(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            relationship_type=payload.relationship_type,
            target_type=payload.target_type,
            target_id=payload.target_id,
            relationship_scope=payload.relationship_scope,
            scope_json=payload.scope_json,
            responsibility_type=payload.responsibility_type,
            effective_from=payload.effective_from or datetime.utcnow(),
            effective_to=payload.effective_to,
            status=LifecycleState.PROPOSED.value,
            metadata_json=payload.metadata_json,
            created_by=self.current_user_id
        )
        self.repo.create(self.db, new_rel)
        await self.audit.publish_relationship_created(new_rel.id, payload.model_dump())
        
        return new_rel, []

    async def update_relationship(self, request_id: str, relationship_id: uuid.UUID, payload: GenericRelationshipUpdate) -> Tuple[Optional[GenericRelationship], List[dict]]:
        existing = self.repo.get_by_id(self.db, relationship_id, self.tenant_id)
        if not existing:
            return None, [{"rule_id": "NOT_FOUND", "message": "Relationship not found"}]

        before_state = {
            "relationship_scope": existing.relationship_scope,
            "scope_json": existing.scope_json,
            "responsibility_type": existing.responsibility_type,
            "effective_from": existing.effective_from.isoformat() if existing.effective_from else None,
            "effective_to": existing.effective_to.isoformat() if existing.effective_to else None,
            "status": existing.status
        }
        
        # Build validation payload
        val_payload = existing.__dict__.copy()
        val_payload.update(payload.model_dump(exclude_unset=True))
        if '_sa_instance_state' in val_payload:
            del val_payload['_sa_instance_state']
        
        validation_results = self.validator.validate_payload(request_id, val_payload, is_update=True, current_status=existing.status)
        has_errors = any(r.status == "FAIL" and r.severity == "ERROR" for r in validation_results)
        if has_errors:
            for r in validation_results:
                if r.status == "FAIL":
                    await self.audit.publish_validation_failed(request_id, r.rule_id, r.message)
            return None, [{"rule_id": r.rule_id, "message": r.message} for r in validation_results if r.status == "FAIL"]

        # Update
        update_data = payload.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(existing, k, v)
            
        existing.updated_by = self.current_user_id
        self.repo.update(self.db, existing)
        
        after_state = payload.model_dump(exclude_unset=True)
        await self.audit.publish_relationship_updated(existing.id, before_state, after_state)
        
        return existing, []

    async def revoke_relationship(self, relationship_id: uuid.UUID, reason: str) -> bool:
        if not reason:
            raise ValueError("Reason is mandatory for revocation")
            
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.REVOKED.value)
        if rel:
            await self.audit.publish_relationship_revoked(relationship_id, reason)
            return True
        return False

    async def suspend_relationship(self, relationship_id: uuid.UUID, reason: str) -> bool:
        if not reason or not reason.strip():
            raise ValueError("Reason is mandatory for suspension")
            
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.SUSPENDED.value)
        if rel:
            await self.audit.publish_relationship_suspended(relationship_id, {"reason": reason})
            return True
        return False

    async def expire_relationship(self, relationship_id: uuid.UUID, reason: str) -> bool:
        if not reason or not reason.strip():
            raise ValueError("Reason for expiration is required")
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.EXPIRED.value, effective_to=datetime.utcnow())
        if rel:
            await self.audit.publish_relationship_expired(relationship_id, {"reason": reason})
            return True
        return False

    async def reject_relationship(self, relationship_id: uuid.UUID, reason: str) -> bool:
        if not reason or not reason.strip():
            raise ValueError("Reason for rejection is required")
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.REJECTED.value)
        if rel:
            await self.audit.publish_relationship_rejected(relationship_id, {"reason": reason, "rejected_by": str(self.current_user_id)})
            return True
        return False

    async def approve_relationship(self, relationship_id: uuid.UUID) -> bool:
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.PENDING_APPROVAL.value)
        if rel:
            rel.approved_by = self.current_user_id
            await self.audit.publish_relationship_approved(relationship_id, {"approved_by": str(self.current_user_id)})
            return True
        return False

    async def activate_relationship(self, relationship_id: uuid.UUID) -> bool:
        rel = self.repo.soft_transition_status(self.db, relationship_id, self.tenant_id, LifecycleState.ACTIVE.value)
        if rel:
            await self.audit.publish_relationship_activated(relationship_id, {})
            return True
        return False

    def search_relationships(self, source_type: str, source_id: str, relationship_type: Optional[str] = None) -> List[GenericRelationship]:
        return self.repo.find_active(self.db, self.tenant_id, source_type, source_id, relationship_type)
