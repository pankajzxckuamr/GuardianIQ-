# Implementation Plan - Prompt 3.4: Implement Safe Rule Evaluator + Decision Combiner (WBS 3.4)

Implement the enterprise safe rule condition evaluator (AST & JSON Expression Engine) with zero arbitrary code execution, supporting allow-listed operators, and the deterministic Decision Combiner enforcing strict precedence (`DENY > REQUIRE_APPROVAL > ESCALATE > ALLOW_WITH_OBLIGATIONS > ALLOW`).

## User Review Required

> [!IMPORTANT]
> **Key Architecture & Security Rules**:
> 1. **Zero Arbitrary Code Execution (Safe Evaluator)**:
>    - Evaluates rule conditions using a recursive, strictly allow-listed AST / JSON-Logic expression evaluator.
>    - Supported operators: `EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `EXISTS`, `CONTAINS`, `ALL`, `ANY`, `NOT`, `AND`, `OR`.
>    - Path extraction supporting dotted notation (`actor.role`, `data.classification`, `tool.operation`, `agent.autonomy_level`).
> 2. **Strict Combining Precedence**:
>    - Enforces deterministic hierarchical decision combining:
>      $$\text{DENY} > \text{REQUIRE\_APPROVAL} > \text{ESCALATE} > \text{ALLOW\_WITH\_OBLIGATIONS} > \text{ALLOW}$$
> 3. **Obligations & Approval Aggregation**:
>    - Aggregates obligations (data field masking, redaction, telemetry) and pending approval requirements when intermediate rules match.
> 4. **Persistence & Explainability**:
>    - Produces `RuleEvaluationDetail` for every evaluated rule with timing (`evaluation_time_ms`), match status, action, and severity.

## Open Questions

- None.

## Proposed Changes

### Policy Engine Rule Evaluator & Combiner

#### [NEW] [backend/app/modules/policy_engine/evaluator.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/evaluator.py)
- Implement `SafeRuleEvaluator`:
  - `evaluate_condition(condition_json, condition_expression, context_dict) -> bool`
  - `evaluate_rule(rule, context_dict) -> RuleEvaluationDetail`
  - Allow-listed operator implementations: `_eval_op(op, left, right, context)`

#### [NEW] [backend/app/modules/policy_engine/combiner.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/combiner.py)
- Implement `DecisionCombiner`:
  - `combine_rule_evaluations(rule_evaluations, policy_metadata) -> GovernedRuntimeResponse`
  - Evaluates decision hierarchy: `DENY` > `REQUIRE_APPROVAL` > `ESCALATE` > `ALLOW_WITH_OBLIGATIONS` > `ALLOW`.
  - Collects violations, obligations, and required approver roles.

#### [MODIFY] [backend/app/modules/enforcement/decision_combiner.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/decision_combiner.py)
- Wire `DecisionCombiner` for the internal enforcement pipeline.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_rule_evaluator_combiner.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_rule_evaluator_combiner.py):
  1. **Safe Operator Suite**: Test all allow-listed operators (`EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `EXISTS`, `CONTAINS`, `ALL`, `ANY`, `NOT`, `AND`, `OR`).
  2. **Security & Sandbox Test**: Ensure malicious payloads (e.g. `__import__`, `eval`, arbitrary syntax) are safely handled and rejected without code execution.
  3. **Decision Combining Precedence Test**:
     - Rules returning `[ALLOW, REQUIRE_APPROVAL, ALLOW]` $\rightarrow$ combines to `REQUIRE_APPROVAL`.
     - Rules returning `[ALLOW, REQUIRE_APPROVAL, DENY]` $\rightarrow$ combines to `DENY`.
     - Rules returning `[MODIFY]` $\rightarrow$ combines to `ALLOW_WITH_OBLIGATIONS` with field redaction payload.
  4. **Detailed Rule Output & Performance**: Verify `RuleEvaluationDetail` contains accurate `evaluation_time_ms` and explainability fields.
