from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.agent_boundary.repository import AgentBoundaryRepository


from app.modules.relationship.cache_service import MemoryCacheService


class AgentBoundaryService:
    def __init__(self, db: Session):
        self.db = db
        self.cache = MemoryCacheService()

    def get_boundary(self, agent_id: UUID, tenant_id: UUID) -> Optional[AgentRuntimeBoundary]:
        return AgentBoundaryRepository.get_by_agent_id(self.db, agent_id, tenant_id)

    def list_boundaries(self, tenant_id: UUID) -> List[AgentRuntimeBoundary]:
        return AgentBoundaryRepository.list_boundaries(self.db, tenant_id)

    def set_boundary(self, tenant_id: UUID, data: Dict[str, Any]) -> AgentRuntimeBoundary:
        agent_id = data["agent_id"]
        existing = AgentBoundaryRepository.get_by_agent_id(self.db, agent_id, tenant_id)
        if existing:
            existing.max_autonomy_level = data.get("max_autonomy_level", existing.max_autonomy_level)
            existing.allowed_access_modes_json = data.get("allowed_access_modes_json", existing.allowed_access_modes_json)
            existing.rate_limit_per_minute = data.get("rate_limit_per_minute", existing.rate_limit_per_minute)
            existing.max_concurrency = data.get("max_concurrency", existing.max_concurrency)
            existing.allow_sub_agent_spawn = data.get("allow_sub_agent_spawn", existing.allow_sub_agent_spawn)
            existing.require_approval_threshold = data.get("require_approval_threshold", existing.require_approval_threshold)
            existing.is_active = data.get("is_active", existing.is_active)
            self.db.commit()
            self.cache.invalidate_tenant(str(tenant_id))
            return existing

        boundary = AgentRuntimeBoundary(
            tenant_id=tenant_id,
            agent_id=agent_id,
            max_autonomy_level=data.get("max_autonomy_level", "HUMAN_SUPERVISED"),
            allowed_access_modes_json=data.get("allowed_access_modes_json", ["READ_ONLY"]),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 120),
            max_concurrency=data.get("max_concurrency", 5),
            allow_sub_agent_spawn=data.get("allow_sub_agent_spawn", False),
            require_approval_threshold=data.get("require_approval_threshold"),
            is_active=data.get("is_active", True),
        )
        AgentBoundaryRepository.create_or_update(self.db, boundary)
        self.db.commit()
        self.cache.invalidate_tenant(str(tenant_id))
        return boundary

    def evaluate_boundary(
        self, tenant_id: UUID, agent_id: UUID, request_context: Dict[str, Any]
    ):
        from app.modules.agent_boundary.resolver import AgentBoundaryResolver
        resolver = AgentBoundaryResolver(self.db)
        return resolver.resolve_and_enforce(tenant_id, agent_id, request_context)

    def evaluate_model_invocation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        model_id: UUID,
        requested_version: Optional[str] = None,
        environment: Optional[str] = None,
        data_classification: Optional[str] = None,
        is_fallback: bool = False,
    ):
        from app.modules.agent_boundary.model_guard import ModelProviderGuard
        guard = ModelProviderGuard(self.db)
        return guard.evaluate_model_invocation(
            tenant_id=tenant_id,
            agent_id=agent_id,
            model_id=model_id,
            requested_version=requested_version,
            environment=environment,
            data_classification=data_classification,
            is_fallback=is_fallback,
        )


