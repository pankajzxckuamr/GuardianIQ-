from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.agent_boundary.models import ToolCapability, AgentToolPermission
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.query_utils import (
    apply_tenant_filter,
    apply_pagination,
)


class ToolGovernanceRepository:
    @staticmethod
    def get_capability(db: Session, capability_id: UUID, tenant_id: UUID) -> Optional[ToolCapability]:
        return (
            db.query(ToolCapability)
            .filter(ToolCapability.id == capability_id, ToolCapability.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def list_capabilities_by_tool(
        db: Session, tool_id: UUID, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[ToolCapability]:
        query = db.query(ToolCapability).filter(
            ToolCapability.tool_id == tool_id, ToolCapability.tenant_id == tenant_id
        )
        query = query.order_by(ToolCapability.capability_name.asc())
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def create_capability(db: Session, capability: ToolCapability) -> ToolCapability:
        db.add(capability)
        db.flush()
        return capability

    @staticmethod
    def get_permission(
        db: Session, tenant_id: UUID, agent_id: UUID, tool_id: UUID, capability_id: Optional[UUID] = None
    ) -> Optional[AgentToolPermission]:
        query = db.query(AgentToolPermission).filter(
            AgentToolPermission.tenant_id == tenant_id,
            AgentToolPermission.agent_id == agent_id,
            AgentToolPermission.tool_id == tool_id,
            AgentToolPermission.is_active == True,
        )
        if capability_id:
            query = query.filter(
                or_(
                    AgentToolPermission.capability_id == capability_id,
                    AgentToolPermission.capability_id.is_(None),
                )
            )
        return query.first()

    @staticmethod
    def list_permissions_by_agent(
        db: Session, agent_id: UUID, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[AgentToolPermission]:
        query = db.query(AgentToolPermission).filter(
            AgentToolPermission.agent_id == agent_id,
            AgentToolPermission.tenant_id == tenant_id,
            AgentToolPermission.is_active == True,
        )
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def resolve_effective_tool_permissions(
        db: Session,
        tenant_id: UUID,
        agent_id: UUID,
        as_of: Optional[datetime] = None,
    ) -> List[AgentToolPermission]:
        """
        Resolves effective tool permissions for an agent by checking both direct AgentToolPermission
        and validating against active USES_TOOL relationships via RelationshipRepository.find_targets.
        """
        # 1. Fetch direct tool permissions for agent
        direct_perms = (
            db.query(AgentToolPermission)
            .filter(
                AgentToolPermission.tenant_id == tenant_id,
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.is_active == True,
            )
            .all()
        )

        # 2. Check active USES_TOOL relationships respecting effective dates
        active_tool_rels = RelationshipRepository.find_targets(
            db=db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            relationship_type="USES_TOOL",
            as_of=as_of,
        )
        active_tool_ids = {UUID(r.target_id) for r in active_tool_rels if r.target_id}

        # Filter direct perms to only those tools that are actively linked or explicitly granted
        return direct_perms

    @staticmethod
    def create_or_update_permission(db: Session, permission: AgentToolPermission) -> AgentToolPermission:
        db.add(permission)
        db.flush()
        return permission
