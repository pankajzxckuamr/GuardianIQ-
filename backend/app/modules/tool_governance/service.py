from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.agent_boundary.models import ToolCapability, AgentToolPermission
from app.modules.tool_governance.repository import ToolGovernanceRepository


class ToolGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def list_capabilities(self, tool_id: UUID, tenant_id: UUID) -> List[ToolCapability]:
        return ToolGovernanceRepository.list_capabilities_by_tool(self.db, tool_id, tenant_id)

    def add_capability(self, tenant_id: UUID, data: Dict[str, Any]) -> ToolCapability:
        capability = ToolCapability(
            tenant_id=tenant_id,
            tool_id=data["tool_id"],
            capability_name=data["capability_name"],
            description=data.get("description"),
            access_mode=data.get("access_mode", "EXECUTE"),
            requires_approval=data.get("requires_approval", False),
            input_schema_json=data.get("input_schema_json"),
            rate_limit=data.get("rate_limit"),
        )
        ToolGovernanceRepository.create_capability(self.db, capability)
        self.db.commit()
        return capability

    def list_agent_permissions(self, agent_id: UUID, tenant_id: UUID) -> List[AgentToolPermission]:
        return ToolGovernanceRepository.list_permissions_by_agent(self.db, agent_id, tenant_id)

    def grant_permission(self, tenant_id: UUID, data: Dict[str, Any]) -> AgentToolPermission:
        perm = AgentToolPermission(
            tenant_id=tenant_id,
            agent_id=data["agent_id"],
            tool_id=data["tool_id"],
            capability_id=data.get("capability_id"),
            permission_level=data.get("permission_level", "EXECUTE"),
            max_calls_per_run=data.get("max_calls_per_run"),
            require_approval=data.get("require_approval", False),
            is_active=data.get("is_active", True),
        )
        ToolGovernanceRepository.create_or_update_permission(self.db, perm)
        self.db.commit()
        return perm

    def evaluate_tool_invocation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_id: UUID,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
    ):
        from app.modules.tool_governance.guard import ToolPermissionGuard
        guard = ToolPermissionGuard(self.db)
        return guard.evaluate_tool_invocation(
            tenant_id=tenant_id,
            agent_id=agent_id,
            tool_id=tool_id,
            operation=operation,
            parameters=parameters,
            environment=environment,
        )

