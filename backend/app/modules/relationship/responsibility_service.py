import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.modules.relationship.models import ObjectResponsibility
from app.modules.relationship.schemas import ObjectResponsibilityCreate, ObjectResponsibilityUpdate
from app.modules.relationship.repository import ResponsibilityRepository
from app.modules.relationship.audit_service import RelationshipAuditService

class ResponsibilityService:
    def __init__(self, db: Session, tenant_id: uuid.UUID, current_user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.repo = ResponsibilityRepository()
        self.audit = RelationshipAuditService(db, current_user_id)

    async def assign_responsibility(self, payload: ObjectResponsibilityCreate) -> ObjectResponsibility:
        # Check if there is an existing primary owner if this is primary OWNER
        previous_assignee = None
        if payload.responsibility_type == "OWNER" and payload.is_primary:
            existing = self.repo.find_primary_owner(self.db, self.tenant_id, payload.object_type, payload.object_id)
            if existing:
                previous_assignee = existing.actor_id
                # Revoke the old primary owner
                self.repo.revoke_assignment(self.db, self.tenant_id, existing.id, datetime.utcnow())

        resp = ObjectResponsibility(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            object_type=payload.object_type,
            object_id=payload.object_id,
            actor_type=payload.actor_type,
            actor_id=payload.actor_id,
            responsibility_type=payload.responsibility_type,
            is_primary=payload.is_primary,
            effective_from=payload.effective_from or datetime.utcnow(),
            effective_to=payload.effective_to,
            status='ACTIVE',
            created_by=self.current_user_id
        )
        self.repo.create(self.db, resp)
        await self.audit.publish_responsibility_assigned(
            payload.object_type, uuid.UUID(payload.object_id) if len(payload.object_id) == 36 else None, 
            payload.responsibility_type, previous_assignee
        )
        return resp

    async def update_assignment(self, responsibility_id: uuid.UUID, payload: ObjectResponsibilityUpdate) -> Optional[ObjectResponsibility]:
        resp = self.repo.find_by_id(self.db, self.tenant_id, responsibility_id)
        if not resp:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(resp, k, v)
        resp.updated_by = self.current_user_id
        
        self.repo.update_assignment(self.db, resp)
        return resp

    async def revoke_assignment(self, responsibility_id: uuid.UUID) -> bool:
        resp = self.repo.revoke_assignment(self.db, self.tenant_id, responsibility_id, datetime.utcnow())
        return resp is not None

    def get_responsibilities_for_object(self, object_type: str, object_id: str) -> List[ObjectResponsibility]:
        return self.repo.find_by_object(self.db, self.tenant_id, object_type, object_id)
