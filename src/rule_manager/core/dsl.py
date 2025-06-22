import re
from typing import Any, Dict, List, Optional, Union
from ..models.base import RuleContext
from ..models.errors import RuleDSLSyntaxError


class DSLEvaluator:
    """
    Safe DSL evaluator for rule conditions.
    Uses a simple expression language to avoid eval/exec security issues.
    """

    def __init__(self):
        self.operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
            "contains": lambda a, b: b in a,
            "startswith": lambda a, b: str(a).startswith(str(b)),
            "endswith": lambda a, b: str(a).endswith(str(b)),
            "matches": lambda a, b: bool(re.match(str(b), str(a))),
        }

        self.logical_operators = {
            "and": lambda a, b: a and b,
            "or": lambda a, b: a or b,
            "not": lambda a: not a,
        }

    def evaluate(self, expression: str, context: RuleContext) -> bool:
        """
        Evaluate a DSL expression against a context.

        Supported expressions:
        - Simple comparisons: user_id == "123"
        - Logical operators: user_id == "123" and model_name == "gpt-4"
        - Complex expressions: prompt_length > 1000 or model_name in ["gpt-4", "claude"]
        """
        if not expression.strip():
            return True

        try:
            return self._evaluate_expression(expression.strip(), context)
        except Exception as e:
            raise RuleDSLSyntaxError(f"Failed to evaluate expression: {e}", expression)

    def _evaluate_expression(self, expr: str, context: RuleContext) -> bool:
        # Handle logical operators
        if " or " in expr:
            parts = expr.split(" or ")
            return any(
                self._evaluate_expression(part.strip(), context) for part in parts
            )

        if " and " in expr:
            parts = expr.split(" and ")
            return all(
                self._evaluate_expression(part.strip(), context) for part in parts
            )

        if expr.startswith("not "):
            return not self._evaluate_expression(expr[4:].strip(), context)

        # Handle parentheses
        if "(" in expr and ")" in expr:
            return self._evaluate_with_parentheses(expr, context)

        # Handle simple comparison
        return self._evaluate_comparison(expr, context)

    def _evaluate_with_parentheses(self, expr: str, context: RuleContext) -> bool:
        # Simple parentheses handling - find innermost parentheses first
        while "(" in expr:
            start = expr.rfind("(")
            end = expr.find(")", start)
            if end == -1:
                raise RuleDSLSyntaxError("Unmatched parentheses", expr)

            inner_expr = expr[start + 1 : end]
            result = self._evaluate_expression(inner_expr, context)
            expr = expr[:start] + str(result) + expr[end + 1 :]

        return self._evaluate_expression(expr, context)

    def _evaluate_comparison(self, expr: str, context: RuleContext) -> bool:
        # Find the operator
        operator = None
        for op in sorted(self.operators.keys(), key=len, reverse=True):
            if op in expr:
                operator = op
                break

        if not operator:
            # No operator found, treat as boolean value
            return self._get_context_value(expr, context)

        parts = expr.split(operator, 1)
        if len(parts) != 2:
            raise RuleDSLSyntaxError(f"Invalid comparison expression", expr)

        left = self._parse_value(parts[0].strip(), context)
        right = self._parse_value(parts[1].strip(), context)

        try:
            return self.operators[operator](left, right)
        except Exception as e:
            raise RuleDSLSyntaxError(f"Error in comparison: {e}", expr)

    def _parse_value(self, value: str, context: RuleContext) -> Any:
        value = value.strip()

        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Handle lists
        if value.startswith("[") and value.endswith("]"):
            items = []
            content = value[1:-1].strip()
            if content:
                # Simple list parsing - split by comma and parse each item
                for item in content.split(","):
                    items.append(self._parse_value(item.strip(), context))
            return items

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle booleans
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "null" or value.lower() == "none":
            return None

        # Handle context variables
        return self._get_context_value(value, context)

    def _get_context_value(self, key: str, context: RuleContext) -> Any:
        # Direct context attributes
        if hasattr(context, key):
            return getattr(context, key)

        # Custom attributes
        if key in context.custom_attributes:
            return context.custom_attributes[key]

        # Nested attribute access (e.g., custom_attributes.key)
        if "." in key:
            parts = key.split(".")
            value = context
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value

        return None

    def validate_expression(self, expression: str) -> List[str]:
        """
        Validate an expression and return a list of issues found.
        Returns empty list if expression is valid.
        """
        issues = []

        if not expression.strip():
            return issues

        try:
            # Try to parse the expression structure
            self._validate_syntax(expression)
        except RuleDSLSyntaxError as e:
            issues.append(e.message)

        return issues

    def _validate_syntax(self, expr: str) -> None:
        """Basic syntax validation"""
        # Check balanced parentheses
        open_count = expr.count("(")
        close_count = expr.count(")")
        if open_count != close_count:
            raise RuleDSLSyntaxError("Unbalanced parentheses")

        # Check for empty expressions in logical operations
        if " and " in expr:
            parts = expr.split(" and ")
            for part in parts:
                if not part.strip():
                    raise RuleDSLSyntaxError("Empty expression in AND operation")

        if " or " in expr:
            parts = expr.split(" or ")
            for part in parts:
                if not part.strip():
                    raise RuleDSLSyntaxError("Empty expression in OR operation")
