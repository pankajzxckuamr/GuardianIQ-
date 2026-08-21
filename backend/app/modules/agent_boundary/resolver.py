from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from decimal import Decimal
from sqlalchemy.orm import Session

from app.modules.agent.models import Agent
from app.modules.agent_boundary.models import AgentRuntimeBoundary
from app.modules.agent_boundary.repository import AgentBoundaryRepository
from app.modules.policy_engine.enums import Decision, AutonomyLevel, AccessMode


AUTONOMY_LEVEL_RANK = {
    "READ_ONLY": 1,
    "RECOMMEND_ONLY": 2,
    "HUMAN_SUPERVISED": 3,
    "SEMI_AUTONOMOUS": 4,
    "AUTONOMOUS": 5,
}


@dataclass
class BoundaryResolutionResult:
    decision: Decision
    is_permitted: bool
    boundary: Optional[AgentRuntimeBoundary] = None
    reason: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    requires_approval: bool = False
    obligations: List[Dict[str, Any]] = field(default_factory=list)


from app.modules.relationship.cache_service import MemoryCacheService


class AgentBoundaryResolver:
    """
    Enterprise Agent Runtime Boundary Resolver.
    Enforces active boundary constraints, kill switch, max autonomy level hierarchy,
    allowed access modes, sub-agent spawning, and financial transaction thresholds.
    """

    def __init__(self, db: Session):
        self.db = db
        self.cache = MemoryCacheService()

    def resolve_boundary(
        self, tenant_id: UUID, agent_id: UUID, as_of: Optional[datetime] = None
    ) -> Optional[AgentRuntimeBoundary]:
        """Resolves active agent runtime boundary strictly respecting tenant isolation and thread-safe caching."""
        cache_key = f"boundary:{tenant_id}:{agent_id}"
        try:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception:
            pass  # Fallback to DB on cache read error

        boundary = AgentBoundaryRepository.get_by_agent_id(self.db, agent_id, tenant_id)
        if boundary is not None:
            try:
                self.cache.set(cache_key, boundary, ttl_seconds=300)
            except Exception:
                pass
        return boundary

    def enforce_boundary(
        self,
        boundary: Optional[AgentRuntimeBoundary],
        agent: Optional[Agent],
        request_context: Dict[str, Any],
    ) -> BoundaryResolutionResult:
        """
        Enforces runtime boundary policies against requested execution context.
        Context can contain:
          - "autonomy_level": requested autonomy level (e.g. "AUTONOMOUS", "RECOMMEND_ONLY")
          - "access_mode": requested access mode (e.g. "WRITE", "EXECUTE", "READ_ONLY")
          - "spawn_sub_agent": boolean flag if agent is attempting to spawn a child agent
          - "transaction_amount": numeric value representing financial or token cost
          - "operation": string name of operation
          - "environment": string (e.g. "PRODUCTION", "STAGING")
        """
        violations: List[str] = []
        requires_approval = False
        obligations: List[Dict[str, Any]] = []

        # 1. Agent Existence & Status Check (Kill Switch)
        if not agent:
            return BoundaryResolutionResult(
                decision=Decision.DENY,
                is_permitted=False,
                boundary=boundary,
                reason="Agent entity not found",
                violations=["AGENT_NOT_FOUND"],
            )

        if agent.status != "ACTIVE":
            return BoundaryResolutionResult(
                decision=Decision.DENY,
                is_permitted=False,
                boundary=boundary,
                reason=f"Agent kill-switch active: Agent status is '{agent.status}'",
                violations=[f"AGENT_STATUS_INACTIVE_{agent.status}"],
            )

        # 2. Boundary Kill Switch & Existence
        if not boundary:
            # Default fallback when no specific boundary record exists
            return BoundaryResolutionResult(
                decision=Decision.ALLOW,
                is_permitted=True,
                boundary=None,
                reason="No custom runtime boundary defined; default execution allowed",
            )

        if not boundary.is_active:
            return BoundaryResolutionResult(
                decision=Decision.DENY,
                is_permitted=False,
                boundary=boundary,
                reason="Agent boundary kill-switch is ACTIVE (boundary.is_active == False)",
                violations=["BOUNDARY_KILL_SWITCH_ACTIVE"],
            )

        # 3. Autonomy Level Hierarchy Check
        max_autonomy = (boundary.max_autonomy_level or "HUMAN_SUPERVISED").upper()
        req_autonomy = (
            request_context.get("autonomy_level")
            or getattr(agent, "execution_mode", None)
            or "HUMAN_SUPERVISED"
        ).upper()

        max_rank = AUTONOMY_LEVEL_RANK.get(max_autonomy, 3)
        req_rank = AUTONOMY_LEVEL_RANK.get(req_autonomy, 3)

        if req_rank > max_rank:
            if max_autonomy in ["READ_ONLY", "RECOMMEND_ONLY"]:
                violations.append(
                    f"Autonomous execution blocked: Agent boundary restricts autonomy to {max_autonomy}"
                )
                return BoundaryResolutionResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    boundary=boundary,
                    reason=f"Requested autonomy '{req_autonomy}' exceeds boundary limit '{max_autonomy}'",
                    violations=violations,
                )
            else:
                requires_approval = True
                violations.append(
                    f"Requested autonomy '{req_autonomy}' exceeds limit '{max_autonomy}', requires human supervision"
                )

        # 4. Allowed Access Modes Check
        req_access_mode = request_context.get("access_mode")
        if req_access_mode:
            allowed_modes = [m.upper() for m in (boundary.allowed_access_modes_json or [])]
            if req_access_mode.upper() not in allowed_modes and "*" not in allowed_modes:
                violations.append(
                    f"Access mode '{req_access_mode}' is not in allowed boundary modes: {allowed_modes}"
                )
                return BoundaryResolutionResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    boundary=boundary,
                    reason=f"Unauthorized access mode '{req_access_mode}'",
                    violations=violations,
                )

        # 5. Sub-Agent Spawning Permission
        if request_context.get("spawn_sub_agent"):
            if not boundary.allow_sub_agent_spawn:
                violations.append("Sub-agent spawning is prohibited by agent boundary")
                return BoundaryResolutionResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    boundary=boundary,
                    reason="Sub-agent spawning is disabled for this agent",
                    violations=violations,
                )

        # 6. Transaction Approval Threshold Check
        tx_amount = request_context.get("transaction_amount")
        if tx_amount is not None and boundary.require_approval_threshold is not None:
            try:
                val = Decimal(str(tx_amount))
                threshold = Decimal(str(boundary.require_approval_threshold))
                if val > threshold:
                    requires_approval = True
                    obligations.append({
                        "type": "REQUIRE_FINANCIAL_APPROVAL",
                        "amount": float(val),
                        "threshold": float(threshold),
                    })
            except Exception:
                pass

        # 7. Rate Limiting Obligation
        if boundary.rate_limit_per_minute:
            obligations.append({
                "type": "ENFORCE_RATE_LIMIT",
                "limit_per_minute": boundary.rate_limit_per_minute,
            })

        # Synthesize Final Boundary Decision
        if violations and not requires_approval:
            return BoundaryResolutionResult(
                decision=Decision.DENY,
                is_permitted=False,
                boundary=boundary,
                reason="; ".join(violations),
                violations=violations,
            )

        if requires_approval:
            return BoundaryResolutionResult(
                decision=Decision.REQUIRE_APPROVAL,
                is_permitted=False,
                boundary=boundary,
                reason="Agent operation requires approval: " + "; ".join(violations or ["Approval threshold exceeded"]),
                violations=violations,
                requires_approval=True,
                obligations=obligations,
            )

        return BoundaryResolutionResult(
            decision=Decision.ALLOW,
            is_permitted=True,
            boundary=boundary,
            reason="Agent execution permitted within boundary constraints",
            obligations=obligations,
        )

    def resolve_and_enforce(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request_context: Dict[str, Any],
        as_of: Optional[datetime] = None,
    ) -> BoundaryResolutionResult:
        """Unified entry point for runtime resolution and boundary enforcement."""
        agent = self.db.query(Agent).filter(Agent.id == agent_id, Agent.tenant_id == tenant_id).first()
        boundary = self.resolve_boundary(tenant_id, agent_id, as_of)
        return self.enforce_boundary(boundary, agent, request_context)
