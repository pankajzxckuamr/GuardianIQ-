from uuid import uuid4
from datetime import datetime, timezone
import pytest

from app.modules.policy_engine.models import PolicyRule
import app.db.base
from app.modules.policy_engine.enums import Decision
from app.modules.policy_engine.evaluator import SafeRuleEvaluator, SafeExpressionEvaluator
from app.modules.policy_engine.combiner import DecisionCombiner
from app.modules.policy_engine.schemas import GovernedRuntimeRequest, ActorContext, AgentContext, ToolContext, DataRequestContext


def test_safe_operator_evaluations():
    context = {
        "actor": {"user_id": "u-123", "role": "ANALYST", "clearance_level": 3},
        "agent": {"agent_id": "a-456", "autonomy_level": "SEMI_AUTONOMOUS"},
        "tool": {"tool_id": "t-789", "operation": "execute_query", "tags": ["prod", "db"]},
        "data": {"classification": "RESTRICTED", "sensitivity_level": "CRITICAL", "record_count": 1500},
    }

    # 1. Comparison operators (EQ, NE, GT, GTE, LT, LTE)
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "actor.role", "operator": "EQ", "value": "ANALYST"}, context
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "data.record_count", "operator": "GT", "value": 1000}, context
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "data.record_count", "operator": "LTE", "value": 1500}, context
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "actor.clearance_level", "operator": "GTE", "value": 3}, context
    )

    # 2. Membership & Existence (IN, CONTAINS, EXISTS)
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "actor.role", "operator": "IN", "value": ["ADMIN", "ANALYST", "DEVELOPER"]}, context
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "tool.tags", "operator": "CONTAINS", "value": "prod"}, context
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {"field": "data.classification", "operator": "EXISTS"}, context
    )

    # 3. Combinators (AND, OR, NOT)
    assert SafeRuleEvaluator.evaluate_condition_json(
        {
            "AND": [
                {"field": "actor.role", "operator": "EQ", "value": "ANALYST"},
                {"field": "data.record_count", "operator": "GT", "value": 500},
            ]
        },
        context,
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {
            "OR": [
                {"field": "actor.role", "operator": "EQ", "value": "ADMIN"},
                {"field": "tool.operation", "operator": "EQ", "value": "execute_query"},
            ]
        },
        context,
    )
    assert SafeRuleEvaluator.evaluate_condition_json(
        {
            "NOT": {"field": "actor.role", "operator": "EQ", "value": "GUEST"}
        },
        context,
    )


def test_ast_expression_security_and_sandbox():
    context = {
        "actor": {"role": "OPERATOR", "level": 5},
        "data": {"count": 250},
    }

    evaluator = SafeExpressionEvaluator(context)

    # Valid Safe Expressions
    assert evaluator.evaluate("actor.role == 'OPERATOR' and data.count > 100") is True
    assert evaluator.evaluate("actor.level <= 3 or data.count == 250") is True
    assert evaluator.evaluate("not (actor.role == 'ADMIN')") is True

    # Malicious injection attempts -> Must fail safely to False without execution
    assert evaluator.evaluate("__import__('os').system('echo pwned')") is False
    assert evaluator.evaluate("eval('1 + 1') == 2") is False
    assert evaluator.evaluate("open('/etc/passwd').read()") is False
    assert evaluator.evaluate("[x for x in ().__class__.__bases__[0].__subclasses__()]") is False


def test_rule_evaluation_detail_output():
    tenant_id = uuid4()
    v_id = uuid4()

    rule = PolicyRule(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_version_id=v_id,
        rule_code="RULE-DLP-01",
        name="Block Bulk Restricted Export",
        rule_type="DATA_ACCESS",
        target_type="DATA_SOURCE",
        target_id="*",
        condition_json={
            "AND": [
                {"field": "data.classification", "operator": "EQ", "value": "RESTRICTED"},
                {"field": "data.record_count", "operator": "GT", "value": 1000},
            ]
        },
        action="DENY",
        severity="CRITICAL",
        execution_order=1,
    )

    req = GovernedRuntimeRequest(
        tenant_id=tenant_id,
        data=DataRequestContext(
            data_source_id=str(uuid4()),
            classification="RESTRICTED",
            record_count=1500,
        ),
    )

    detail = SafeRuleEvaluator.evaluate_rule(rule, req)
    assert detail.rule_code == "RULE-DLP-01"
    assert detail.matched is True
    assert detail.action == "DENY"
    assert detail.severity == "CRITICAL"
    assert detail.evaluation_time_ms >= 0.0


def test_decision_combiner_strict_precedence():
    tenant_id = uuid4()
    p_id = uuid4()
    r_deny = SafeRuleEvaluator.evaluate_rule(
        PolicyRule(id=uuid4(), rule_code="R-DENY", action="DENY", severity="HIGH"), {}
    )
    r_approval = SafeRuleEvaluator.evaluate_rule(
        PolicyRule(id=uuid4(), rule_code="R-APP", action="REQUIRE_APPROVAL", severity="MEDIUM"), {}
    )
    r_escalate = SafeRuleEvaluator.evaluate_rule(
        PolicyRule(id=uuid4(), rule_code="R-ESC", action="ESCALATE", severity="HIGH"), {}
    )
    r_modify = SafeRuleEvaluator.evaluate_rule(
        PolicyRule(id=uuid4(), rule_code="R-MOD", action="MODIFY", severity="LOW"), {}
    )
    r_allow = SafeRuleEvaluator.evaluate_rule(
        PolicyRule(id=uuid4(), rule_code="R-ALLOW", action="ALLOW", severity="LOW"), {}
    )

    # 1. ALLOW + REQUIRE_APPROVAL -> REQUIRE_APPROVAL
    res1 = DecisionCombiner.combine([
        {"policy_id": p_id, "policy_code": "POL-1", "rule_evaluations": [r_allow, r_approval]}
    ])
    assert res1.decision == Decision.REQUIRE_APPROVAL
    assert len(res1.approval_requirements) == 1

    # 2. ALLOW + REQUIRE_APPROVAL + DENY -> DENY (DENY wins over REQUIRE_APPROVAL)
    res2 = DecisionCombiner.combine([
        {"policy_id": p_id, "policy_code": "POL-1", "rule_evaluations": [r_allow, r_approval, r_deny]}
    ])
    assert res2.decision == Decision.DENY
    assert len(res2.violations) == 1

    # 3. ALLOW + ESCALATE -> ESCALATE
    res3 = DecisionCombiner.combine([
        {"policy_id": p_id, "policy_code": "POL-1", "rule_evaluations": [r_allow, r_escalate]}
    ])
    assert res3.decision == Decision.ESCALATE

    # 4. ESCALATE + REQUIRE_APPROVAL -> REQUIRE_APPROVAL (REQUIRE_APPROVAL > ESCALATE)
    res4 = DecisionCombiner.combine([
        {"policy_id": p_id, "policy_code": "POL-1", "rule_evaluations": [r_escalate, r_approval]}
    ])
    assert res4.decision == Decision.REQUIRE_APPROVAL

    # 5. MODIFY -> ALLOW_WITH_OBLIGATIONS
    res5 = DecisionCombiner.combine([
        {"policy_id": p_id, "policy_code": "POL-1", "rule_evaluations": [r_modify]}
    ])
    assert res5.decision == Decision.ALLOW_WITH_OBLIGATIONS
    assert len(res5.obligations) == 1
