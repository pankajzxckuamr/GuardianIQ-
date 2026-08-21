from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from decimal import Decimal
from sqlalchemy.orm import Session

from app.modules.registry.models import Tool
from app.modules.agent_boundary.models import ToolCapability, AgentToolPermission
from app.modules.relationship.repository import RelationshipRepository
from app.modules.tool_governance.repository import ToolGovernanceRepository
from app.modules.policy_engine.enums import Decision, AccessMode


ACCESS_MODE_HIERARCHY = {
    "READ": 1,
    "READ_ONLY": 1,
    "EXECUTE": 2,
    "WRITE": 3,
    "ADMIN": 4,
}


@dataclass
class ToolGuardResult:
    decision: Decision
    is_permitted: bool
    capability: Optional[ToolCapability] = None
    permission: Optional[AgentToolPermission] = None
    reason: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    requires_approval: bool = False
    obligations: List[Dict[str, Any]] = field(default_factory=list)


class ToolPermissionGuard:
    """
    Enterprise Tool Capability & Permission Guard.
    Enforces active USES_TOOL graph relationship prerequisite, capability existence,
    access mode boundaries (READ cannot execute WRITE), parameter constraints,
    and approval interception. Replaces ad hoc string blocked-lists.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_tool_invocation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_id: UUID,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> ToolGuardResult:
        now = as_of or datetime.now(timezone.utc)
        violations: List[str] = []
        requires_approval = False
        obligations: List[Dict[str, Any]] = []

        # 1. Prerequisite: Active USES_TOOL / USES Relationship Check
        rels = RelationshipRepository.find_active(
            db=self.db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            as_of=now,
        )
        has_tool_rel = any(
            (r.relationship_type in ["USES_TOOL", "USES"])
            and (r.target_type == "TOOL" or r.relationship_type == "USES_TOOL")
            and (r.target_id == str(tool_id))
            for r in rels
        )

        if not has_tool_rel:
            violations.append(
                f"Relationship prerequisite failed: Agent {agent_id} has no active USES_TOOL link to tool {tool_id}"
            )
            return ToolGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Agent is not authorized to use this tool (no active relationship)",
                violations=violations,
            )

        # 2. Tool Existence & Status Check
        tool = self.db.query(Tool).filter(Tool.id == tool_id, Tool.tenant_id == tenant_id).first()
        if not tool or tool.status != "ACTIVE":
            violations.append(f"Tool {tool_id} is not active or does not exist")
            return ToolGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason=f"Tool is inactive or not found",
                violations=violations,
            )

        # 3. Match Granular Tool Capability from Backfill/Registry
        capabilities = ToolGovernanceRepository.list_capabilities_by_tool(self.db, tool_id, tenant_id)
        capability: Optional[ToolCapability] = None
        for cap in capabilities:
            if cap.capability_name.lower() == operation.lower():
                capability = cap
                break

        if not capability:
            violations.append(f"Tool capability '{operation}' does not exist on tool '{tool.tool_name}'")
            return ToolGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason=f"Operation '{operation}' is not a registered capability of tool '{tool.tool_name}'",
                violations=violations,
            )

        # 4. Check Agent Tool Permission (if explicitly configured)
        perms = ToolGovernanceRepository.list_permissions_by_agent(self.db, agent_id, tenant_id)
        matching_perm: Optional[AgentToolPermission] = None
        for p in perms:
            if p.tool_id == tool_id:
                if p.capability_id == capability.id or p.capability_id is None:
                    matching_perm = p
                    break

        if matching_perm:
            if not matching_perm.is_active:
                violations.append(f"Agent tool permission for {tool.tool_name} is INACTIVE / REVOKED")
                return ToolGuardResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    capability=capability,
                    permission=matching_perm,
                    reason="Agent tool permission is revoked",
                    violations=violations,
                )

            # Access Mode Hierarchical Check on Permission Level
            perm_level = (matching_perm.permission_level or "EXECUTE").upper()
            cap_mode = (capability.access_mode or "EXECUTE").upper()

            perm_rank = ACCESS_MODE_HIERARCHY.get(perm_level, 2)
            cap_rank = ACCESS_MODE_HIERARCHY.get(cap_mode, 2)

            if perm_rank < cap_rank:
                violations.append(
                    f"Access mode violation: Agent permission level '{perm_level}' is insufficient for capability mode '{cap_mode}'"
                )
                return ToolGuardResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    capability=capability,
                    permission=matching_perm,
                    reason=f"Agent permission '{perm_level}' cannot execute '{cap_mode}' capability",
                    violations=violations,
                )

            if matching_perm.require_approval:
                requires_approval = True

        # 5. Capability Approval Requirement Check
        if capability.requires_approval:
            requires_approval = True

        # 6. Parameter Constraints & Schema Validation
        if parameters and capability.input_schema_json:
            schema = capability.input_schema_json
            # Required fields check
            required_fields = schema.get("required", [])
            for rf in required_fields:
                if rf not in parameters or parameters[rf] is None:
                    violations.append(f"Missing required parameter '{rf}' for operation '{operation}'")

            # Max value constraints
            max_val = schema.get("max_value")
            if max_val is not None and "amount" in parameters:
                try:
                    if Decimal(str(parameters["amount"])) > Decimal(str(max_val)):
                        violations.append(
                            f"Parameter 'amount' ({parameters['amount']}) exceeds maximum permitted value ({max_val})"
                        )
                except Exception:
                    pass

            # Prohibited parameters check
            prohibited = schema.get("prohibited", [])
            for pf in prohibited:
                if pf in parameters:
                    violations.append(f"Parameter '{pf}' is prohibited for operation '{operation}'")

            if violations:
                return ToolGuardResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    capability=capability,
                    permission=matching_perm,
                    reason="; ".join(violations),
                    violations=violations,
                )

        # 7. Rate Limit Obligation
        if capability.rate_limit:
            obligations.append({
                "type": "ENFORCE_TOOL_RATE_LIMIT",
                "tool_id": str(tool_id),
                "operation": operation,
                "rate_limit": capability.rate_limit,
            })

        # Synthesize Decision
        if requires_approval:
            return ToolGuardResult(
                decision=Decision.REQUIRE_APPROVAL,
                is_permitted=False,
                capability=capability,
                permission=matching_perm,
                reason=f"Tool operation '{operation}' requires authorization approval",
                requires_approval=True,
                obligations=obligations,
            )

        return ToolGuardResult(
            decision=Decision.ALLOW,
            is_permitted=True,
            capability=capability,
            permission=matching_perm,
            reason=f"Tool operation '{operation}' authorized",
            obligations=obligations,
        )
