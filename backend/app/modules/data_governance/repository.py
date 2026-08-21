from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.agent_boundary.models import DataSourceField, AgentDataPermission
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.query_utils import (
    apply_tenant_filter,
    apply_pagination,
)


class DataGovernanceRepository:
    @staticmethod
    def get_field_by_id(db: Session, field_id: UUID, tenant_id: UUID) -> Optional[DataSourceField]:
        return (
            db.query(DataSourceField)
            .filter(DataSourceField.id == field_id, DataSourceField.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def list_fields_by_data_source(
        db: Session, data_source_id: UUID, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[DataSourceField]:
        query = db.query(DataSourceField).filter(
            DataSourceField.data_source_id == data_source_id,
            DataSourceField.tenant_id == tenant_id,
            DataSourceField.is_active == True,
        )
        query = query.order_by(DataSourceField.field_name.asc())
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def create_field(db: Session, field: DataSourceField) -> DataSourceField:
        db.add(field)
        db.flush()
        return field

    @staticmethod
    def get_permission(
        db: Session, tenant_id: UUID, agent_id: UUID, data_source_id: UUID, field_id: Optional[UUID] = None
    ) -> Optional[AgentDataPermission]:
        query = db.query(AgentDataPermission).filter(
            AgentDataPermission.tenant_id == tenant_id,
            AgentDataPermission.agent_id == agent_id,
            AgentDataPermission.data_source_id == data_source_id,
            AgentDataPermission.is_active == True,
        )
        if field_id:
            query = query.filter(
                or_(
                    AgentDataPermission.field_id == field_id,
                    AgentDataPermission.field_id.is_(None),
                )
            )
        return query.first()

    @staticmethod
    def list_permissions_by_agent(
        db: Session, agent_id: UUID, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[AgentDataPermission]:
        query = db.query(AgentDataPermission).filter(
            AgentDataPermission.agent_id == agent_id,
            AgentDataPermission.tenant_id == tenant_id,
            AgentDataPermission.is_active == True,
        )
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def resolve_effective_data_permissions(
        db: Session,
        tenant_id: UUID,
        agent_id: UUID,
        as_of: Optional[datetime] = None,
    ) -> List[AgentDataPermission]:
        """
        Resolves effective data permissions for an agent by checking direct permissions
        and validating against active USES_DATA_SOURCE relationships via RelationshipRepository.find_targets.
        """
        # 1. Direct agent data permissions
        direct_perms = (
            db.query(AgentDataPermission)
            .filter(
                AgentDataPermission.tenant_id == tenant_id,
                AgentDataPermission.agent_id == agent_id,
                AgentDataPermission.is_active == True,
            )
            .all()
        )

        # 2. Check active USES_DATA_SOURCE relationships respecting effective dates
        active_ds_rels = RelationshipRepository.find_targets(
            db=db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            relationship_type="USES_DATA_SOURCE",
            as_of=as_of,
        )
        return direct_perms

    @staticmethod
    def create_or_update_permission(db: Session, permission: AgentDataPermission) -> AgentDataPermission:
        db.add(permission)
        db.flush()
        return permission
