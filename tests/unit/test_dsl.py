import pytest

from rule_manager.core.dsl import DSLEvaluator
from rule_manager.models.base import RuleContext
from rule_manager.models.errors import RuleDSLSyntaxError


class TestDSLEvaluator:
    def setup_method(self):
        self.evaluator = DSLEvaluator()
        self.context = RuleContext(
            user_id="user123",
            project_id="project456",
            model_name="gpt-4",
            prompt_length=1500,
            custom_attributes={
                "environment": "production",
                "user_role": "admin",
                "available_models": ["gpt-4", "gpt-3.5-turbo", "claude"],
                "user_clearance_level": 5,
            },
        )

    def test_simple_equality_comparison(self):
        assert self.evaluator.evaluate('user_id == "user123"', self.context) is True
        assert self.evaluator.evaluate('user_id == "other_user"', self.context) is False
        assert self.evaluator.evaluate('model_name == "gpt-4"', self.context) is True

    def test_numeric_comparisons(self):
        assert self.evaluator.evaluate("prompt_length > 1000", self.context) is True
        assert self.evaluator.evaluate("prompt_length > 2000", self.context) is False
        assert self.evaluator.evaluate("prompt_length >= 1500", self.context) is True
        assert self.evaluator.evaluate("prompt_length < 2000", self.context) is True
        assert self.evaluator.evaluate("prompt_length <= 1500", self.context) is True

    def test_in_operator(self):
        assert (
            self.evaluator.evaluate('model_name in ["gpt-4", "claude"]', self.context)
            is True
        )
        assert (
            self.evaluator.evaluate('model_name in ["gpt-3.5-turbo"]', self.context)
            is False
        )
        assert (
            self.evaluator.evaluate('user_id in ["user123", "user456"]', self.context)
            is True
        )

    def test_not_in_operator(self):
        assert (
            self.evaluator.evaluate('model_name not in ["gpt-3.5-turbo"]', self.context)
            is True
        )
        assert (
            self.evaluator.evaluate(
                'model_name not in ["gpt-4", "claude"]', self.context
            )
            is False
        )

    def test_contains_operator(self):
        context = RuleContext(custom_attributes={"text": "hello world"})
        assert (
            self.evaluator.evaluate('custom_attributes.text contains "world"', context)
            is True
        )
        assert (
            self.evaluator.evaluate('custom_attributes.text contains "xyz"', context)
            is False
        )

    def test_string_methods(self):
        assert (
            self.evaluator.evaluate('user_id startswith "user"', self.context) is True
        )
        assert self.evaluator.evaluate('user_id endswith "123"', self.context) is True
        assert (
            self.evaluator.evaluate('user_id startswith "admin"', self.context) is False
        )

    def test_logical_and_operator(self):
        expr = 'user_id == "user123" and model_name == "gpt-4"'
        assert self.evaluator.evaluate(expr, self.context) is True

        expr = 'user_id == "user123" and model_name == "claude"'
        assert self.evaluator.evaluate(expr, self.context) is False

    def test_logical_or_operator(self):
        expr = 'user_id == "other_user" or model_name == "gpt-4"'
        assert self.evaluator.evaluate(expr, self.context) is True

        expr = 'user_id == "other_user" or model_name == "claude"'
        assert self.evaluator.evaluate(expr, self.context) is False

    def test_logical_not_operator(self):
        assert (
            self.evaluator.evaluate('not user_id == "other_user"', self.context) is True
        )
        assert (
            self.evaluator.evaluate('not user_id == "user123"', self.context) is False
        )

    def test_complex_logical_expression(self):
        expr = (
            'user_id == "user123" and (model_name == "gpt-4" or prompt_length > 2000)'
        )
        assert self.evaluator.evaluate(expr, self.context) is True

        expr = 'user_id == "other_user" and (model_name == "gpt-4" or prompt_length > 2000)'
        assert self.evaluator.evaluate(expr, self.context) is False

    def test_custom_attributes_access(self):
        assert (
            self.evaluator.evaluate(
                'custom_attributes.environment == "production"', self.context
            )
            is True
        )
        assert (
            self.evaluator.evaluate(
                'custom_attributes.user_role == "admin"', self.context
            )
            is True
        )
        assert (
            self.evaluator.evaluate(
                "custom_attributes.user_clearance_level >= 3", self.context
            )
            is True
        )

    def test_nested_attribute_access(self):
        # Test direct custom attribute access
        assert (
            self.evaluator.evaluate('environment == "production"', self.context) is True
        )
        assert self.evaluator.evaluate('user_role == "admin"', self.context) is True

    def test_list_handling(self):
        assert (
            self.evaluator.evaluate("model_name in available_models", self.context)
            is True
        )

        context_with_list = RuleContext(
            custom_attributes={"models": ["gpt-4", "claude"]}
        )
        assert (
            self.evaluator.evaluate(
                'custom_attributes.models contains "gpt-4"', context_with_list
            )
            is True
        )

    def test_boolean_values(self):
        context = RuleContext(custom_attributes={"enabled": True, "disabled": False})
        assert (
            self.evaluator.evaluate("custom_attributes.enabled == true", context)
            is True
        )
        assert (
            self.evaluator.evaluate("custom_attributes.disabled == false", context)
            is True
        )

    def test_null_values(self):
        context = RuleContext(user_id=None)
        assert self.evaluator.evaluate("user_id == null", context) is True
        assert self.evaluator.evaluate("user_id != null", context) is False

    def test_empty_expression(self):
        assert self.evaluator.evaluate("", self.context) is True
        assert self.evaluator.evaluate("   ", self.context) is True

    def test_parentheses_handling(self):
        expr = (
            '(user_id == "user123" and model_name == "gpt-4") or prompt_length > 2000'
        )
        assert self.evaluator.evaluate(expr, self.context) is True

        expr = '(user_id == "other_user" and model_name == "gpt-4") or prompt_length > 2000'
        assert self.evaluator.evaluate(expr, self.context) is False

    def test_validation_empty_expression(self):
        issues = self.evaluator.validate_expression("")
        assert len(issues) == 0

    def test_validation_unbalanced_parentheses(self):
        issues = self.evaluator.validate_expression("(user_id == 'test'")
        assert len(issues) > 0
        assert "parentheses" in issues[0].lower()

    def test_validation_empty_logical_parts(self):
        issues = self.evaluator.validate_expression("user_id == 'test' and ")
        assert len(issues) > 0

    def test_syntax_error_handling(self):
        with pytest.raises(RuleDSLSyntaxError):
            self.evaluator.evaluate("invalid syntax here", self.context)

    def test_missing_context_value(self):
        # Should return None for missing values
        result = self.evaluator.evaluate('missing_field == "test"', self.context)
        assert result is False

    def test_numeric_string_parsing(self):
        assert self.evaluator.evaluate("prompt_length > 1000", self.context) is True
        assert self.evaluator.evaluate("prompt_length == 1500", self.context) is True
        assert self.evaluator.evaluate("prompt_length == 1500.0", self.context) is True

    def test_matches_operator(self):
        context = RuleContext(user_id="user123")
        assert self.evaluator.evaluate('user_id matches "user\\d+"', context) is True
        assert self.evaluator.evaluate('user_id matches "admin\\w+"', context) is False
