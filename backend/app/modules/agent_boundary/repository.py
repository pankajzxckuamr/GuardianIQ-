from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.policy_engine.query_utils import (
    apply_tenant_filter,
    apply_pagination,
)


class AgentBoundaryRepository:
    @staticmethod
    def get_by_agent_id(
        db: Session, agent_id: UUID, tenant_id: UUID, active_only: bool = False
    ) -> Optional[AgentRuntimeBoundary]:
        query = db.query(AgentRuntimeBoundary).filter(
            AgentRuntimeBoundary.agent_id == agent_id,
            AgentRuntimeBoundary.tenant_id == tenant_id,
        )
        if active_only:
            query = query.filter(AgentRuntimeBoundary.is_active == True)
        return query.first()

    @staticmethod
    def list_boundaries(
        db: Session, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[AgentRuntimeBoundary]:
        query = db.query(AgentRuntimeBoundary)
        query = apply_tenant_filter(query, AgentRuntimeBoundary, tenant_id)
        query = query.order_by(AgentRuntimeBoundary.created_at.desc())
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def create_or_update(db: Session, boundary: AgentRuntimeBoundary) -> AgentRuntimeBoundary:
        db.add(boundary)
        db.flush()
        return boundary
