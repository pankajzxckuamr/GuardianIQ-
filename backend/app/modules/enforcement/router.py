from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.modules.policy_engine.schemas import (
    GovernedRuntimeRequest,
    GovernedRuntimeResponse,
    EnforcementMode,
    DataOperation,
)
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder
from app.modules.enforcement.engine import RuntimeEnforcementEngine

router = APIRouter(prefix="/api/v1/enforce", tags=["v1 Runtime Enforcement"])


class SimulationRequestPayload(BaseModel):
    agent_id: str
    actor_id: Optional[str] = None
    role: Optional[str] = "OPERATOR"
    workflow_id: Optional[str] = None
    model_id: Optional[str] = None
    operation: Optional[str] = "EXECUTE"
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_parameters: Optional[Dict[str, Any]] = None
    data_source_id: Optional[str] = None
    table_name: Optional[str] = None
    columns: Optional[List[str]] = None
    data_operation: Optional[str] = "READ"
    environment: Optional[str] = "PRODUCTION"
    facts: Optional[Dict[str, Any]] = None


@router.post("/simulate", response_model=StandardResponse[dict])
def simulate_enforcement(
    payload: SimulationRequestPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Non-authoritative runtime evaluation simulation.
    Evaluates hard boundaries, tool capability guards, data access permissions,
    model safety boundaries, dynamic AST policies, and combiner semantics with zero target side-effects.
    """
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    actor_id = payload.actor_id or str(current_user.id)

    data_requests = []
    if payload.data_source_id:
        data_requests.append({
            "data_source_id": payload.data_source_id,
            "table_name": payload.table_name,
            "columns": payload.columns or [],
            "operation": DataOperation[payload.data_operation.upper()] if payload.data_operation and payload.data_operation.upper() in DataOperation.__members__ else DataOperation.READ,
        })

    governed_req = GovernedRuntimeContextBuilder.build_request(
        tenant_id=tenant_id,
        actor_id=actor_id,
        role=payload.role,
        agent_id=payload.agent_id,
        workflow_id=payload.workflow_id,
        model_id=payload.model_id,
        operation=payload.operation,
        tool_id=payload.tool_id,
        tool_name=payload.tool_name,
        tool_parameters=payload.tool_parameters,
        data_requests=data_requests if data_requests else None,
        environment=payload.environment,
        facts=payload.facts,
        enforcement_mode=EnforcementMode.DRY_RUN,  # Non-blocking simulation mode
    )

    engine = RuntimeEnforcementEngine(db)
    response = engine.enforce(governed_req, tenant_id, timeout_ms=2000)

    # Compute remediation hints for non-ALLOW outcomes
    trace_steps = response.trace.get("steps", []) if isinstance(response.trace, dict) else []
    boundary_step = next((s for s in trace_steps if "BOUNDARY" in s.get("layer", "")), None)
    tool_step = next((s for s in trace_steps if "TOOL" in s.get("layer", "")), None)
    data_step = next((s for s in trace_steps if "DATA" in s.get("layer", "")), None)
    model_step = next((s for s in trace_steps if "MODEL" in s.get("layer", "")), None)

    all_violations = []
    if response.violations:
        all_violations.extend([v.model_dump() if hasattr(v, "model_dump") else str(v) for v in response.violations])
    if boundary_step and boundary_step.get("violations"):
        all_violations.extend(boundary_step.get("violations"))
    if boundary_step and boundary_step.get("reason") and not all_violations:
        all_violations.append(boundary_step.get("reason"))

    remediation_hints = []
    if not response.execution_permitted:
        for v in all_violations:
            v_msg = str(v)
            if "USES_TOOL" in v_msg:
                remediation_hints.append("Grant tool access by binding agent to tool with USES_TOOL relationship in Registry.")
            elif "autonomy" in v_msg.lower():
                remediation_hints.append("Increase agent max autonomy level or submit request for human approval.")
            elif "classification" in v_msg.lower():
                remediation_hints.append("Agent classification ceiling is below required data classification. Request exception or adjust data source ceiling.")
            elif "kill-switch" in v_msg.lower() or "kill switch" in v_msg.lower():
                remediation_hints.append("Emergency kill-switch is active. Deactivate kill-switch on agent boundary tab to resume operations.")
            else:
                remediation_hints.append(f"Remediate boundary violation: {v_msg}")

    structured_trace = {
        "steps": trace_steps,
        "boundary_check": {
            "evaluated": boundary_step is not None,
            "permitted": boundary_step.get("decision") == "ALLOW" if boundary_step else True,
            "reasons": [boundary_step.get("reason")] if boundary_step and boundary_step.get("reason") else [],
            "violations": boundary_step.get("violations", []) if boundary_step else [],
            "kill_switch_active": any("kill" in str(v).lower() for v in (boundary_step.get("violations", []) if boundary_step else [])),
        },
        "tool_guard": {
            "evaluated": tool_step is not None,
            "permitted": tool_step.get("decision") == "ALLOW" if tool_step else True,
            "reason": tool_step.get("reason") if tool_step else None,
        },
        "data_guard": {
            "evaluated": data_step is not None,
            "permitted": data_step.get("decision") == "ALLOW" if data_step else True,
            "reason": data_step.get("reason") if data_step else None,
        },
        "model_guard": {
            "evaluated": model_step is not None,
            "permitted": model_step.get("decision") == "ALLOW" if model_step else True,
            "reason": model_step.get("reason") if model_step else None,
        },
        "combiner": {
            "combined_decision": response.decision.value,
            "precedence_applied": "DENY > REQUIRE_APPROVAL > ESCALATE > ALLOW_WITH_OBLIGATIONS > ALLOW",
        },
    }

    return ResponseHelper.success(
        message="Enforcement simulation evaluated successfully",
        data={
            "request_id": str(response.request_id),
            "correlation_id": str(response.correlation_id),
            "decision": response.decision.value,
            "execution_permitted": response.execution_permitted,
            "reasons": response.reasons,
            "obligations": response.obligations,
            "violations": all_violations,
            "remediation_hints": remediation_hints,
            "trace": structured_trace,
        },
    )
