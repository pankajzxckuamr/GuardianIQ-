from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, update
from datetime import datetime
from app.modules.relationship.models import GenericRelationship, ObjectResponsibility
from app.modules.relationship.constants import LifecycleState

class RelationshipRepository:
    @staticmethod
    def create(db: Session, relationship: GenericRelationship) -> GenericRelationship:
        db.add(relationship)
        db.flush()
        return relationship

    @staticmethod
    def get_by_id(db: Session, relationship_id: UUID, tenant_id: UUID) -> Optional[GenericRelationship]:
        stmt = select(GenericRelationship).where(
            and_(
                GenericRelationship.id == relationship_id,
                GenericRelationship.tenant_id == tenant_id
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_active(db: Session, tenant_id: UUID, source_type: str, source_id: str, relationship_type: Optional[str] = None, as_of: Optional[datetime] = None) -> List[GenericRelationship]:
        conditions = [
            GenericRelationship.tenant_id == tenant_id,
            GenericRelationship.source_type == source_type,
            GenericRelationship.source_id == source_id,
            GenericRelationship.status != LifecycleState.ARCHIVED.value
        ]
        if relationship_type:
            conditions.append(GenericRelationship.relationship_type == relationship_type)
        if as_of:
            conditions.append(or_(GenericRelationship.effective_from <= as_of, GenericRelationship.effective_from.is_(None)))
            conditions.append(or_(GenericRelationship.effective_to >= as_of, GenericRelationship.effective_to.is_(None)))
            
        stmt = select(GenericRelationship).where(and_(*conditions))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def find_targets(db: Session, tenant_id: UUID, source_type: str, source_id: str, relationship_type: str, scope: Optional[str] = None, as_of: Optional[datetime] = None) -> List[GenericRelationship]:
        conditions = [
            GenericRelationship.tenant_id == tenant_id,
            GenericRelationship.source_type == source_type,
            GenericRelationship.source_id == source_id,
            GenericRelationship.relationship_type == relationship_type,
            GenericRelationship.status != LifecycleState.ARCHIVED.value
        ]
        if scope:
            conditions.append(GenericRelationship.relationship_scope == scope)
        if as_of:
            conditions.append(or_(GenericRelationship.effective_from <= as_of, GenericRelationship.effective_from.is_(None)))
            conditions.append(or_(GenericRelationship.effective_to >= as_of, GenericRelationship.effective_to.is_(None)))
            
        stmt = select(GenericRelationship).where(and_(*conditions))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def find_reverse(db: Session, tenant_id: UUID, target_type: str, target_id: str, relationship_type: Optional[str] = None) -> List[GenericRelationship]:
        conditions = [
            GenericRelationship.tenant_id == tenant_id,
            GenericRelationship.target_type == target_type,
            GenericRelationship.target_id == target_id,
            GenericRelationship.status != LifecycleState.ARCHIVED.value
        ]
        if relationship_type:
            conditions.append(GenericRelationship.relationship_type == relationship_type)
            
        stmt = select(GenericRelationship).where(and_(*conditions))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update(db: Session, relationship: GenericRelationship) -> GenericRelationship:
        # Assumes object is already attached to session
        db.flush()
        return relationship

    @staticmethod
    def soft_transition_status(db: Session, relationship_id: UUID, tenant_id: UUID, new_status: str, effective_to: Optional[datetime] = None) -> Optional[GenericRelationship]:
        rel = RelationshipRepository.get_by_id(db, relationship_id, tenant_id)
        if rel:
            rel.status = new_status
            if effective_to:
                rel.effective_to = effective_to
            db.flush()
        return rel


class ResponsibilityRepository:
    @staticmethod
    def create(db: Session, responsibility: ObjectResponsibility) -> ObjectResponsibility:
        db.add(responsibility)
        db.flush()
        return responsibility

    @staticmethod
    def find_by_object(db: Session, tenant_id: UUID, object_type: str, object_id: str) -> List[ObjectResponsibility]:
        stmt = select(ObjectResponsibility).where(
            and_(
                ObjectResponsibility.tenant_id == tenant_id,
                ObjectResponsibility.object_type == object_type,
                ObjectResponsibility.object_id == object_id,
                ObjectResponsibility.status != 'ARCHIVED'
            )
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def find_primary_owner(db: Session, tenant_id: UUID, object_type: str, object_id: str) -> Optional[ObjectResponsibility]:
        stmt = select(ObjectResponsibility).where(
            and_(
                ObjectResponsibility.tenant_id == tenant_id,
                ObjectResponsibility.object_type == object_type,
                ObjectResponsibility.object_id == object_id,
                ObjectResponsibility.responsibility_type == 'OWNER',
                ObjectResponsibility.is_primary == True,
                ObjectResponsibility.status != 'ARCHIVED'
            )
        )
        return db.execute(stmt).scalar_one_or_none()
        
    @staticmethod
    def find_by_id(db: Session, tenant_id: UUID, responsibility_id: UUID) -> Optional[ObjectResponsibility]:
        stmt = select(ObjectResponsibility).where(
            and_(
                ObjectResponsibility.id == responsibility_id,
                ObjectResponsibility.tenant_id == tenant_id
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update_assignment(db: Session, responsibility: ObjectResponsibility) -> ObjectResponsibility:
        db.flush()
        return responsibility

    @staticmethod
    def revoke_assignment(db: Session, tenant_id: UUID, responsibility_id: UUID, effective_to: datetime) -> Optional[ObjectResponsibility]:
        resp = ResponsibilityRepository.find_by_id(db, tenant_id, responsibility_id)
        if resp:
            resp.status = 'REVOKED'
            resp.effective_to = effective_to
            resp.is_primary = False
            db.flush()
        return resp
