import ast
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from app.modules.policy_engine.enums import Decision
from app.modules.policy_engine.models import PolicyRule
from app.modules.policy_engine.schemas import RuleEvaluationDetail, GovernedRuntimeRequest


class SafeExpressionEvaluator:
    """
    Secure AST Visitor that evaluates simple boolean/comparison expressions
    without arbitrary code execution (no eval, no builtins, no function calls).
    """

    ALLOWED_OPERATORS = {
        ast.Eq: lambda a, b: a == b,
        ast.NotEq: lambda a, b: a != b,
        ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b,
        ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b,
        ast.In: lambda a, b: a in b if b is not None else False,
        ast.NotIn: lambda a, b: a not in b if b is not None else True,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
    }

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def evaluate(self, expr_str: str) -> bool:
        if not expr_str or expr_str.strip() in ["", "true", "True"]:
            return True
        if expr_str.strip() in ["false", "False"]:
            return False

        try:
            tree = ast.parse(expr_str, mode="eval")
            return bool(self._eval_node(tree.body))
        except Exception:
            return False

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            return self._resolve_path(node.id)

        elif isinstance(node, ast.Attribute):
            full_path = self._get_attribute_path(node)
            return self._resolve_path(full_path)

        elif isinstance(node, ast.List):
            return [self._eval_node(elem) for elem in node.elts]

        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem) for elem in node.elts)

        elif isinstance(node, ast.Set):
            return {self._eval_node(elem) for elem in node.elts}

        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k): self._eval_node(v)
                for k, v in zip(node.keys, node.values)
            }

        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return not self._eval_node(node.operand)
            elif isinstance(node.op, ast.USub):
                return -self._eval_node(node.operand)
            elif isinstance(node.op, ast.UAdd):
                return +self._eval_node(node.operand)
            raise ValueError(f"Unsupported UnaryOp: {type(node.op)}")

        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError(f"Unsupported BoolOp: {type(node.op)}")

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_func = self.ALLOWED_OPERATORS.get(type(op))
                if not op_func:
                    raise ValueError(f"Unsupported Comparison Op: {type(op)}")
                try:
                    if not op_func(left, right):
                        return False
                except Exception:
                    return False
                left = right
            return True

        else:
            raise ValueError(f"Disallowed AST Node: {type(node).__name__}")

    def _get_attribute_path(self, node: ast.Attribute) -> str:
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))

    def _resolve_path(self, path: str) -> Any:
        keys = path.split(".")
        val = self.context
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            elif hasattr(val, k):
                val = getattr(val, k)
            else:
                return None
        return val


class SafeRuleEvaluator:
    """
    Enterprise Safe Rule Evaluator.
    Evaluates policy rules against GovernedRuntimeRequest or context dictionary
    supporting allow-listed AST expressions and JSON logic predicates.
    """

    OPERATORS = {
        "EQ": lambda a, b: a == b,
        "==": lambda a, b: a == b,
        "NE": lambda a, b: a != b,
        "!=": lambda a, b: a != b,
        "GT": lambda a, b: (a is not None and b is not None) and a > b,
        ">": lambda a, b: (a is not None and b is not None) and a > b,
        "GTE": lambda a, b: (a is not None and b is not None) and a >= b,
        ">=": lambda a, b: (a is not None and b is not None) and a >= b,
        "LT": lambda a, b: (a is not None and b is not None) and a < b,
        "<": lambda a, b: (a is not None and b is not None) and a < b,
        "LTE": lambda a, b: (a is not None and b is not None) and a <= b,
        "<=": lambda a, b: (a is not None and b is not None) and a <= b,
        "IN": lambda a, b: (b is not None) and (a in b if isinstance(b, (list, tuple, set, str, dict)) else False),
        "NOT_IN": lambda a, b: (b is None) or (a not in b if isinstance(b, (list, tuple, set, str, dict)) else True),
        "CONTAINS": lambda a, b: (a is not None) and (b in a if isinstance(a, (list, tuple, set, str, dict)) else False),
        "EXISTS": lambda a, _: a is not None and a != "",
        "NOT_EXISTS": lambda a, _: a is None or a == "",
    }

    @classmethod
    def evaluate_condition_json(cls, condition_json: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not condition_json:
            return True

        # Handle combinators: AND, OR, NOT, ALL, ANY
        if "AND" in condition_json or "and" in condition_json or "ALL" in condition_json or "all" in condition_json:
            sub = condition_json.get("AND") or condition_json.get("and") or condition_json.get("ALL") or condition_json.get("all")
            return all(cls.evaluate_condition_json(c, context) for c in sub)

        if "OR" in condition_json or "or" in condition_json or "ANY" in condition_json or "any" in condition_json:
            sub = condition_json.get("OR") or condition_json.get("or") or condition_json.get("ANY") or condition_json.get("any")
            return any(cls.evaluate_condition_json(c, context) for c in sub)

        if "NOT" in condition_json or "not" in condition_json:
            sub = condition_json.get("NOT") or condition_json.get("not")
            return not cls.evaluate_condition_json(sub, context)

        # Single predicate: { "field": "...", "operator": "...", "value": "..." }
        field_path = condition_json.get("field")
        op = condition_json.get("operator", "EQ").upper()
        target_val = condition_json.get("value")

        if field_path:
            actual_val = cls._resolve_path(field_path, context)
            op_func = cls.OPERATORS.get(op)
            if not op_func:
                return False
            try:
                return op_func(actual_val, target_val)
            except Exception:
                return False

        # Support key-value equality fallback: { "actor.role": "ADMIN" }
        for k, v in condition_json.items():
            if k.upper() not in ["AND", "OR", "NOT", "ALL", "ANY", "FIELD", "OPERATOR", "VALUE"]:
                if cls._resolve_path(k, context) != v:
                    return False
        return True

    @classmethod
    def evaluate_rule(
        cls, rule: PolicyRule, context: Union[GovernedRuntimeRequest, Dict[str, Any]]
    ) -> RuleEvaluationDetail:
        t0 = time.perf_counter()

        if isinstance(context, GovernedRuntimeRequest):
            ctx_dict = context.model_dump()
        else:
            ctx_dict = dict(context)

        matched = False
        error_msg = None

        try:
            # 1. Target check if not wildcard
            if rule.target_id and rule.target_id != "*":
                target_matched = False
                if rule.target_type == "AGENT" and ctx_dict.get("agent", {}).get("agent_id") == rule.target_id:
                    target_matched = True
                elif rule.target_type == "TOOL" and ctx_dict.get("tool", {}).get("tool_id") == rule.target_id:
                    target_matched = True
                elif rule.target_type in ["DATA_SOURCE", "DATASOURCE"] and ctx_dict.get("data", {}).get("data_source_id") == rule.target_id:
                    target_matched = True
                elif rule.target_type == "WORKFLOW" and ctx_dict.get("workflow", {}).get("workflow_id") == rule.target_id:
                    target_matched = True
                elif rule.target_type in ["MODEL", "AI_MODEL"] and ctx_dict.get("model", {}).get("model_id") == rule.target_id:
                    target_matched = True
                elif not rule.target_type or rule.target_type == "GENERAL":
                    target_matched = True

                if not target_matched:
                    matched = False
                else:
                    matched = True
            else:
                matched = True

            # 2. Evaluate condition_json if present
            if matched and rule.condition_json:
                matched = cls.evaluate_condition_json(rule.condition_json, ctx_dict)

            # 3. Evaluate condition_expression if present
            if matched and rule.condition_expression:
                evaluator = SafeExpressionEvaluator(ctx_dict)
                matched = evaluator.evaluate(rule.condition_expression)

        except Exception as e:
            matched = False
            error_msg = str(e)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)

        # Map action to Decision
        act_str = (rule.action or "ALLOW").upper()
        if act_str == "DENY":
            dec = Decision.DENY
        elif act_str == "REQUIRE_APPROVAL":
            dec = Decision.REQUIRE_APPROVAL
        elif act_str == "ESCALATE":
            dec = Decision.ESCALATE
        elif act_str in ["MODIFY", "ALLOW_WITH_OBLIGATIONS"]:
            dec = Decision.ALLOW_WITH_OBLIGATIONS
        else:
            dec = Decision.ALLOW

        return RuleEvaluationDetail(
            rule_id=str(rule.id),
            rule_name=rule.name if hasattr(rule, "name") else None,
            rule_code=rule.rule_code,
            rule_type=rule.rule_type if hasattr(rule, "rule_type") else "GENERAL",
            matched=matched,
            decision=dec,
            action=rule.action,
            severity=rule.severity,
            evaluation_order=rule.execution_order if hasattr(rule, "execution_order") and rule.execution_order else 0,
            evaluation_time_ms=elapsed_ms,
            error_message=error_msg,
        )

    @classmethod
    def _resolve_path(cls, path: str, context: Dict[str, Any]) -> Any:
        keys = path.split(".")
        val = context
        for k in keys:
            if isinstance(val, dict):
                if k == "data" and val.get("data") is None and val.get("data_requests"):
                    val = val["data_requests"][0]
                else:
                    val = val.get(k)
            elif hasattr(val, k):
                val = getattr(val, k)
            else:
                return None

        if hasattr(val, "value"):
            return val.value
        return val
