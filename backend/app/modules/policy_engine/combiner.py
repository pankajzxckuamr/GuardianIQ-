from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.modules.policy_engine.enums import Decision
from app.modules.policy_engine.schemas import (
    RuleEvaluationDetail,
    ViolationDetail,
    ApprovalRequirement,
    PolicyEvaluationResult,
    GovernedRuntimeResponse,
)


class DecisionCombiner:
    """
    Enterprise Decision Combiner.
    Enforces strict hierarchical decision precedence:
    DENY > REQUIRE_APPROVAL > ESCALATE > ALLOW_WITH_OBLIGATIONS > ALLOW
    Aggregates violations, obligations, approval requirements, and detailed evaluations.
    """

    PRECEDENCE_ORDER = {
        Decision.DENY: 1,
        "DENY": 1,
        Decision.REQUIRE_APPROVAL: 2,
        "REQUIRE_APPROVAL": 2,
        Decision.ESCALATE: 3,
        "ESCALATE": 3,
        Decision.ALLOW_WITH_OBLIGATIONS: 4,
        "ALLOW_WITH_OBLIGATIONS": 4,
        "MODIFY": 4,
        Decision.ALLOW: 5,
        "ALLOW": 5,
    }

    @classmethod
    def combine(
        cls,
        evaluations_by_policy: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[Union[str, UUID]] = None,
        correlation_id: Optional[UUID] = None,
        request: Optional[GovernedRuntimeRequest] = None,
        policy_results: Optional[List[PolicyEvaluationResult]] = None,
        trace: Optional[Dict[str, Any]] = None,
    ) -> GovernedRuntimeResponse:
        """
        Combines rule evaluations or PolicyEvaluationResults across all resolved policies/layers
        into a final GovernedRuntimeResponse.
        """
        now = datetime.now(timezone.utc)
        highest_decision_rank = 5
        final_decision = Decision.ALLOW

        all_violations: List[Union[ViolationDetail, str]] = []
        all_obligations: List[Dict[str, Any]] = []
        all_approvals: List[ApprovalRequirement] = []
        policy_eval_results: List[PolicyEvaluationResult] = []

        total_rules_evaluated = 0

        # Case 1: Combining direct PolicyEvaluationResult objects
        if policy_results is not None:
            for pres in policy_results:
                policy_eval_results.append(pres)
                p_rank = cls.PRECEDENCE_ORDER.get(pres.decision, 5)
                if p_rank < highest_decision_rank:
                    highest_decision_rank = p_rank
                    final_decision = pres.decision

                if pres.violations:
                    all_violations.extend(pres.violations)
                if pres.obligations:
                    all_obligations.extend(pres.obligations)
                if pres.approval_requirements:
                    all_approvals.extend(pres.approval_requirements)
                total_rules_evaluated += len(pres.rule_evaluations or pres.rules_evaluated or [])

        # Case 2: Combining evaluations_by_policy dicts
        elif evaluations_by_policy is not None:
            for pol_eval in evaluations_by_policy:
                p_id = str(pol_eval["policy_id"])
                p_code = pol_eval.get("policy_code", "UNKNOWN")
                v_num = pol_eval.get("version_number", 1)
                rule_evals: List[RuleEvaluationDetail] = pol_eval.get("rule_evaluations", [])

                policy_decision_rank = 5
                policy_decision = Decision.ALLOW
                policy_violations: List[Union[ViolationDetail, str]] = []
                policy_obligations: List[Dict[str, Any]] = []
                policy_approvals: List[ApprovalRequirement] = []

            for r_detail in rule_evals:
                total_rules_evaluated += 1
                if not r_detail.matched:
                    continue

                action = (r_detail.action or "ALLOW").upper()

                if action == "DENY":
                    policy_decision_rank = min(policy_decision_rank, 1)
                    policy_decision = Decision.DENY
                    policy_violations.append(
                        ViolationDetail(
                            rule_code=r_detail.rule_code,
                            message=f"Rule {r_detail.rule_code} triggered DENY enforcement",
                            severity=r_detail.severity,
                        )
                    )

                elif action == "REQUIRE_APPROVAL":
                    policy_decision_rank = min(policy_decision_rank, 2)
                    if policy_decision_rank > 1:
                        policy_decision = Decision.REQUIRE_APPROVAL
                    policy_approvals.append(
                        ApprovalRequirement(
                            approval_type="POLICY_RULE_MATCH",
                            required_role="SECURITY_OFFICER",
                            timeout_minutes=60,
                            metadata_json={"rule_code": r_detail.rule_code},
                        )
                    )

                elif action == "ESCALATE":
                    policy_decision_rank = min(policy_decision_rank, 3)
                    if policy_decision_rank > 2:
                        policy_decision = Decision.ESCALATE
                    policy_approvals.append(
                        ApprovalRequirement(
                            approval_type="SECURITY_ESCALATION",
                            required_role="SECURITY_LEAD",
                            timeout_minutes=30,
                            metadata_json={"rule_code": r_detail.rule_code},
                        )
                    )

                elif action in ["MODIFY", "ALLOW_WITH_OBLIGATIONS"]:
                    policy_decision_rank = min(policy_decision_rank, 4)
                    if policy_decision_rank > 3:
                        policy_decision = Decision.ALLOW_WITH_OBLIGATIONS
                    policy_obligations.append({
                        "type": "TRANSFORM_DATA",
                        "rule_code": r_detail.rule_code,
                        "severity": r_detail.severity,
                    })

                elif action == "ALLOW":
                    pass

            # Update global decision precedence
            if policy_decision_rank < highest_decision_rank:
                highest_decision_rank = policy_decision_rank
                final_decision = policy_decision

            all_violations.extend(policy_violations)
            all_obligations.extend(policy_obligations)
            all_approvals.extend(policy_approvals)

            policy_eval_results.append(
                PolicyEvaluationResult(
                    policy_id=p_id,
                    policy_code=p_code,
                    version_number=v_num,
                    decision=policy_decision,
                    rule_evaluations=rule_evals,
                    violations=policy_violations,
                    obligations=policy_obligations,
                    approval_requirements=policy_approvals,
                )
            )

        # Rationale string construction
        if final_decision == Decision.DENY:
            rationale = f"Enforcement DENIED by {len(all_violations)} blocking rule violation(s)."
        elif final_decision == Decision.REQUIRE_APPROVAL:
            rationale = f"Action intercepted: requires approval from {len(all_approvals)} gate(s)."
        elif final_decision == Decision.ESCALATE:
            rationale = f"Action escalated for high-severity security oversight."
        elif final_decision == Decision.ALLOW_WITH_OBLIGATIONS:
            rationale = f"Action ALLOWED with {len(all_obligations)} operational obligation(s) applied."
        else:
            rationale = f"Action ALLOWED across {total_rules_evaluated} evaluated rule(s)."

        resp_req_id = request.request_id if request else (UUID(str(request_id)) if request_id else uuid4())
        resp_corr_id = request.correlation_id if request else (correlation_id or uuid4())
        is_permitted = final_decision in [Decision.ALLOW, Decision.ALLOW_WITH_OBLIGATIONS]

        return GovernedRuntimeResponse(
            request_id=resp_req_id,
            correlation_id=resp_corr_id,
            decision=final_decision,
            reason=rationale,
            execution_permitted=is_permitted,
            violations=all_violations,
            obligations=all_obligations,
            approval_requirements=all_approvals,
            policy_evaluations=policy_eval_results,
            trace=trace or {},
            enforced_at=now,
            evaluated_at=now,
        )
