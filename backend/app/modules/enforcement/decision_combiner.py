from typing import List
from app.modules.policy_engine.enums import Decision
from app.modules.policy_engine.schemas import PolicyEvaluationResult
from app.modules.policy_engine.combiner import DecisionCombiner


class EnforcementDecisionCombiner:
    """
    Combines individual policy and boundary evaluation decisions into a single composite decision.
    Precedence order: DENY > REQUIRE_APPROVAL > ESCALATE > ALLOW_WITH_OBLIGATIONS/MODIFY > ALLOW.
    """

    @staticmethod
    def combine(evaluations: List[PolicyEvaluationResult]) -> Decision:
        if not evaluations:
            return Decision.ALLOW

        decisions = [e.decision for e in evaluations]

        if Decision.DENY in decisions or "DENY" in decisions:
            return Decision.DENY
        if Decision.REQUIRE_APPROVAL in decisions or "REQUIRE_APPROVAL" in decisions:
            return Decision.REQUIRE_APPROVAL
        if Decision.ESCALATE in decisions or "ESCALATE" in decisions:
            return Decision.ESCALATE
        if Decision.ALLOW_WITH_OBLIGATIONS in decisions or "ALLOW_WITH_OBLIGATIONS" in decisions or "MODIFY" in decisions:
            return Decision.ALLOW_WITH_OBLIGATIONS
        return Decision.ALLOW

