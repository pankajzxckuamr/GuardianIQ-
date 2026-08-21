import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.policy_engine.schemas import (
    GovernedRuntimeRequest,
    GovernedRuntimeResponse,
    PolicyEvaluationResult,
    RuleEvaluationDetail,
    ApprovalRequirement,
)
from app.modules.policy_engine.enums import Decision
from app.modules.policy_engine.resolver import BindingResolver
from app.modules.policy_engine.evaluator import SafeRuleEvaluator
from app.modules.policy_engine.combiner import DecisionCombiner
from app.modules.agent_boundary.resolver import AgentBoundaryResolver
from app.modules.tool_governance.guard import ToolPermissionGuard
from app.modules.data_governance.guard import DataPermissionGuard
from app.modules.agent_boundary.model_guard import ModelProviderGuard
from app.modules.agent_boundary.models import RuntimeAuthorization, RuntimeEnforcementLog


class RuntimeEnforcementEngine:
    """
    Enterprise Unified Runtime Enforcement Engine.
    Executes multi-layered governance:
      - Layer 1: Context Normalization
      - Layer 2: Hard Boundary & Relationship Guards (Agent, Tool, Data, Model)
      - Layer 3: Dynamic Policy Engine (Binding Resolver + AST Rule Evaluator)
      - Layer 4: Decision Combining with Layer-by-Layer Trace & Obligations
    """

    def __init__(self, db: Session):
        self.db = db
        self.agent_boundary_resolver = AgentBoundaryResolver(db)
        self.tool_guard = ToolPermissionGuard(db)
        self.data_guard = DataPermissionGuard(db)
        self.model_guard = ModelProviderGuard(db)
        self.binding_resolver = BindingResolver(db)

    def enforce(
        self,
        request: GovernedRuntimeRequest,
        tenant_id: UUID,
        as_of: Optional[datetime] = None,
        timeout_ms: int = 500,
    ) -> GovernedRuntimeResponse:
        start_time = time.perf_counter()
        now = as_of or datetime.now(timezone.utc)

        layer_results: List[PolicyEvaluationResult] = []
        violations: List[str] = []
        reasons: List[str] = []
        obligations: List[Dict[str, Any]] = []
        approval_requirements: List[ApprovalRequirement] = []
        trace_steps: List[Dict[str, Any]] = []

        agent_uuid: Optional[UUID] = None
        if request.agent and request.agent.agent_id:
            try:
                agent_uuid = UUID(request.agent.agent_id)
            except Exception:
                pass

        try:
            # ---------------------------------------------------------------------
            # LAYER 2A: Agent Runtime Boundary Evaluation
            # ---------------------------------------------------------------------
            if agent_uuid:
                boundary_ctx = {
                    "autonomy_level": request.agent.autonomy_level if request.agent else None,
                    "access_mode": request.tool.access_mode.value if (request.tool and request.tool.access_mode) else None,
                    "spawn_sub_agent": request.facts.get("spawn_sub_agent", False),
                    "transaction_amount": request.facts.get("transaction_amount"),
                    "environment": request.facts.get("environment"),
                    "operation": request.facts.get("operation") or request.operation,
                }
                boundary_res = self.agent_boundary_resolver.resolve_and_enforce(
                    tenant_id=tenant_id,
                    agent_id=agent_uuid,
                    request_context=boundary_ctx,
                    as_of=now,
                )
                trace_steps.append({
                    "layer": "LAYER_2A_AGENT_BOUNDARY",
                    "decision": boundary_res.decision.value,
                    "reason": boundary_res.reason,
                    "violations": boundary_res.violations,
                })
                if boundary_res.decision != Decision.ALLOW:
                    violations.extend(boundary_res.violations)
                    if boundary_res.reason:
                        reasons.append(f"Agent Boundary: {boundary_res.reason}")

                if boundary_res.obligations:
                    obligations.extend(boundary_res.obligations)

                if boundary_res.requires_approval:
                    approval_requirements.append(
                        ApprovalRequirement(
                            approval_type="AGENT_BOUNDARY",
                            reason=boundary_res.reason or "Agent operation requires boundary approval",
                        )
                    )

                # Record Layer 2A Result
                layer_results.append(
                    PolicyEvaluationResult(
                        policy_id=str(boundary_res.boundary.id) if boundary_res.boundary else "AGENT_BOUNDARY",
                        policy_name="Agent Runtime Boundary Guard",
                        decision=boundary_res.decision,
                        reason=boundary_res.reason,
                        violations=boundary_res.violations,
                        obligations=boundary_res.obligations,
                    )
                )

            # ---------------------------------------------------------------------
            # LAYER 2B: Tool Permission & Capability Guard
            # ---------------------------------------------------------------------
            if request.tool and request.tool.tool_id and agent_uuid:
                try:
                    tool_uuid = UUID(request.tool.tool_id)
                    op_name = (
                        request.facts.get("operation")
                        or request.operation
                        or request.tool.tool_name
                        or "execute"
                    )
                    tool_res = self.tool_guard.evaluate_tool_invocation(
                        tenant_id=tenant_id,
                        agent_id=agent_uuid,
                        tool_id=tool_uuid,
                        operation=op_name,
                        parameters=request.tool.parameters,
                        environment=request.facts.get("environment"),
                        as_of=now,
                    )
                    trace_steps.append({
                        "layer": "LAYER_2B_TOOL_GUARD",
                        "decision": tool_res.decision.value,
                        "reason": tool_res.reason,
                        "violations": tool_res.violations,
                    })
                    if tool_res.decision != Decision.ALLOW:
                        violations.extend(tool_res.violations)
                        if tool_res.reason:
                            reasons.append(f"Tool Guard: {tool_res.reason}")

                    if tool_res.obligations:
                        obligations.extend(tool_res.obligations)

                    if tool_res.requires_approval:
                        approval_requirements.append(
                            ApprovalRequirement(
                                approval_type="TOOL_INVOCATION",
                                reason=tool_res.reason or "Tool execution requires approval",
                            )
                        )

                    layer_results.append(
                        PolicyEvaluationResult(
                            policy_id=str(tool_uuid),
                            policy_name="Tool Capability & Permission Guard",
                            decision=tool_res.decision,
                            reason=tool_res.reason,
                            violations=tool_res.violations,
                            obligations=tool_res.obligations,
                        )
                    )
                except Exception as ex:
                    violations.append(f"Tool evaluation error: {str(ex)}")

            # ---------------------------------------------------------------------
            # LAYER 2C: Data Permission & Transformation Guard
            # ---------------------------------------------------------------------
            if request.data_requests and agent_uuid:
                for dr in request.data_requests:
                    try:
                        ds_uuid = UUID(dr.data_source_id)
                        data_res = self.data_guard.evaluate_data_access(
                            tenant_id=tenant_id,
                            agent_id=agent_uuid,
                            data_source_id=ds_uuid,
                            operation=dr.operation.value if hasattr(dr.operation, "value") else str(dr.operation),
                            requested_fields=dr.columns,
                            record_count=dr.record_count,
                            as_of=now,
                        )
                        trace_steps.append({
                            "layer": "LAYER_2C_DATA_GUARD",
                            "data_source_id": str(ds_uuid),
                            "decision": data_res.decision.value,
                            "reason": data_res.reason,
                            "violations": data_res.violations,
                            "transformations": data_res.transformation_map,
                        })
                        if data_res.decision != Decision.ALLOW:
                            violations.extend(data_res.violations)
                            if data_res.reason:
                                reasons.append(f"Data Guard: {data_res.reason}")

                        if data_res.obligations:
                            obligations.extend(data_res.obligations)

                        layer_results.append(
                            PolicyEvaluationResult(
                                policy_id=str(ds_uuid),
                                policy_name="Data Access & Transformation Guard",
                                decision=data_res.decision,
                                reason=data_res.reason,
                                violations=data_res.violations,
                                obligations=data_res.obligations,
                            )
                        )
                    except Exception as ex:
                        violations.append(f"Data evaluation error: {str(ex)}")

            # ---------------------------------------------------------------------
            # LAYER 2D: Model & Provider Guard
            # ---------------------------------------------------------------------
            if request.model and request.model.model_id and agent_uuid:
                try:
                    model_uuid = UUID(request.model.model_id)
                    model_res = self.model_guard.evaluate_model_invocation(
                        tenant_id=tenant_id,
                        agent_id=agent_uuid,
                        model_id=model_uuid,
                        requested_version=request.model.model_version,
                        environment=request.facts.get("environment"),
                        data_classification=request.facts.get("data_classification"),
                        as_of=now,
                    )
                    trace_steps.append({
                        "layer": "LAYER_2D_MODEL_GUARD",
                        "decision": model_res.decision.value,
                        "reason": model_res.reason,
                        "violations": model_res.violations,
                    })
                    if model_res.decision != Decision.ALLOW:
                        violations.extend(model_res.violations)
                        if model_res.reason:
                            reasons.append(f"Model Guard: {model_res.reason}")

                    if model_res.obligations:
                        obligations.extend(model_res.obligations)

                    layer_results.append(
                        PolicyEvaluationResult(
                            policy_id=str(model_uuid),
                            policy_name="Model & Provider Guard",
                            decision=model_res.decision,
                            reason=model_res.reason,
                            violations=model_res.violations,
                            obligations=model_res.obligations,
                        )
                    )
                except Exception as ex:
                    violations.append(f"Model evaluation error: {str(ex)}")

            # ---------------------------------------------------------------------
            # LAYER 3: Dynamic Policy Engine (Binding Resolution + Safe Rule Evaluator)
            # ---------------------------------------------------------------------
            if agent_uuid:
                resolved_set = self.binding_resolver.resolve_runtime_policies(
                    tenant_id=tenant_id,
                    agent_id=str(agent_uuid),
                    tool_ids=[request.tool.tool_id] if (request.tool and request.tool.tool_id) else None,
                    data_source_ids=[dr.data_source_id for dr in request.data_requests] if request.data_requests else None,
                    model_id=request.model.model_id if request.model else None,
                    workflow_id=request.workflow.workflow_id if request.workflow else None,
                    as_of=now,
                )

                for rp in resolved_set.resolved_policies:
                    p_decision = Decision.ALLOW
                    p_violations: List[str] = []
                    p_obligations: List[Dict[str, Any]] = []
                    p_rule_details: List[RuleEvaluationDetail] = []

                    for rule in rp.rules:
                        r_detail = SafeRuleEvaluator.evaluate_rule(rule, request)
                        p_rule_details.append(r_detail)

                        if r_detail.matched:
                            if r_detail.action == "DENY":
                                p_decision = Decision.DENY
                                p_violations.append(f"Rule {r_detail.rule_code} ({r_detail.rule_name}) matched DENY")
                            elif r_detail.action == "REQUIRE_APPROVAL" and p_decision != Decision.DENY:
                                p_decision = Decision.REQUIRE_APPROVAL
                                approval_requirements.append(
                                    ApprovalRequirement(
                                        approval_type="POLICY_RULE",
                                        reason=f"Rule {r_detail.rule_code} required approval",
                                    )
                                )
                            elif r_detail.action in ["MODIFY", "ALLOW_WITH_OBLIGATIONS"] and p_decision not in [Decision.DENY, Decision.REQUIRE_APPROVAL]:
                                p_decision = Decision.ALLOW_WITH_OBLIGATIONS

                    v_num = getattr(rp.version, "version_number", getattr(rp.version, "version_no", 1))
                    trace_steps.append({
                        "layer": "LAYER_3_DYNAMIC_POLICY",
                        "policy_id": str(rp.policy.id),
                        "policy_version_id": str(rp.version.id),
                        "version_no": v_num,
                        "decision": p_decision.value,
                        "rules_evaluated": len(p_rule_details),
                    })

                    if p_decision != Decision.ALLOW:
                        violations.extend(p_violations)
                        reasons.append(f"Policy Engine: Policy '{rp.policy.name}' (v{v_num}) evaluated as {p_decision.value}")

                    layer_results.append(
                        PolicyEvaluationResult(
                            policy_id=str(rp.policy.id),
                            policy_version_id=str(rp.version.id),
                            policy_name=rp.policy.name,
                            decision=p_decision,
                            rules_evaluated=p_rule_details,
                            violations=p_violations,
                            obligations=p_obligations,
                        )
                    )

            # ---------------------------------------------------------------------
            # LAYER 4: Multi-Layer Decision Combining
            # ---------------------------------------------------------------------
            final_response = DecisionCombiner.combine(
                request=request,
                policy_results=layer_results,
                trace={
                    "steps": trace_steps,
                    "total_layers": len(trace_steps),
                    "evaluation_start": now.isoformat(),
                },
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            final_response.latency_ms = elapsed_ms

            # Timeout Enforcement (Fail-Closed)
            if elapsed_ms > timeout_ms:
                return GovernedRuntimeResponse(
                    request_id=request.request_id,
                    correlation_id=request.correlation_id,
                    decision=Decision.DENY,
                    reason=f"Evaluation exceeded timeout of {timeout_ms}ms ({elapsed_ms:.1f}ms elapsed)",
                    reasons=[f"Timeout limit reached: {timeout_ms}ms"],
                    violations=["ENGINE_TIMEOUT_FAIL_CLOSED"],
                    execution_permitted=False,
                    latency_ms=elapsed_ms,
                )

            # Merge additional accumulated obligations and approval requirements
            if obligations:
                final_response.obligations.extend(obligations)
            if approval_requirements:
                final_response.approval_requirements.extend(approval_requirements)
            if reasons:
                final_response.reasons.extend(reasons)

            # ---------------------------------------------------------------------
            # PERSISTENCE: Runtime Authorization & Enforcement Log
            # ---------------------------------------------------------------------
            try:
                if agent_uuid:
                    log_entry = RuntimeEnforcementLog(
                        tenant_id=tenant_id,
                        request_id=str(request.request_id),
                        correlation_id=request.correlation_id,
                        agent_id=agent_uuid,
                        tool_id=UUID(request.tool.tool_id) if (request.tool and request.tool.tool_id) else None,
                        decision=final_response.decision.value,
                        action_taken="ENFORCE_" + final_response.decision.value,
                        latency_ms=elapsed_ms,
                    )
                    self.db.add(log_entry)
                    self.db.commit()
            except Exception:
                self.db.rollback()

            return final_response

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return GovernedRuntimeResponse(
                request_id=request.request_id,
                correlation_id=request.correlation_id,
                decision=Decision.DENY,
                reason=f"Runtime evaluation failed: {str(e)}",
                reasons=[f"Evaluation error: {str(e)}"],
                violations=["EVALUATION_ERROR_FAIL_CLOSED"],
                execution_permitted=False,
                latency_ms=elapsed_ms,
            )
