import pytest
from datetime import datetime
from pydantic import ValidationError

from rule_manager.models.base import (
    Rule,
    RuleSet,
    RuleScope,
    RuleAction,
    RuleContext,
    RuleEvaluationResult,
    RuleEvaluationSummary,
    PriorityTieBreaking,
)


class TestRuleModel:
    def test_create_valid_rule(self):
        rule = Rule(
            name="test_rule",
            scope=RuleScope.GLOBAL,
            priority=50,
            action=RuleAction.ALLOW,
            conditions={"user_id": "user_id == 'test'"},
            parameters={"message": "Test rule"},
        )

        assert rule.name == "test_rule"
        assert rule.scope == RuleScope.GLOBAL
        assert rule.priority == 50
        assert rule.action == RuleAction.ALLOW
        assert rule.enabled is True
        assert rule.conditions == {"user_id": "user_id == 'test'"}
        assert rule.parameters == {"message": "Test rule"}

    def test_rule_priority_validation(self):
        # Valid priority
        rule = Rule(
            name="test_rule",
            scope=RuleScope.GLOBAL,
            action=RuleAction.ALLOW,
            priority=75,
        )
        assert rule.priority == 75

        # Invalid priority (too high)
        with pytest.raises(ValidationError):
            Rule(
                name="test_rule",
                scope=RuleScope.GLOBAL,
                action=RuleAction.ALLOW,
                priority=150,
            )

        # Invalid priority (negative)
        with pytest.raises(ValidationError):
            Rule(
                name="test_rule",
                scope=RuleScope.GLOBAL,
                action=RuleAction.ALLOW,
                priority=-1,
            )

    def test_rule_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            Rule(
                name="test_rule",
                scope=RuleScope.GLOBAL,
                action=RuleAction.ALLOW,
                invalid_field="should_fail",
            )

    def test_rule_inheritance_fields(self):
        rule = Rule(
            name="child_rule",
            scope=RuleScope.PROJECT,
            action=RuleAction.MODIFY,
            parent_rule="parent_rule",
            inherits_from=["base_rule1", "base_rule2"],
        )

        assert rule.parent_rule == "parent_rule"
        assert rule.inherits_from == ["base_rule1", "base_rule2"]


class TestRuleSetModel:
    def test_create_valid_ruleset(self):
        rules = [
            Rule(name="rule1", scope=RuleScope.GLOBAL, action=RuleAction.ALLOW),
            Rule(name="rule2", scope=RuleScope.GLOBAL, action=RuleAction.DENY),
        ]

        ruleset = RuleSet(
            scope=RuleScope.GLOBAL, rules=rules, metadata={"created_by": "test"}
        )

        assert ruleset.scope == RuleScope.GLOBAL
        assert len(ruleset.rules) == 2
        assert ruleset.metadata == {"created_by": "test"}
        assert ruleset.ruleset_version == "1.1"
        assert ruleset.engine_min_version == ">=2.8.0"

    def test_empty_ruleset(self):
        ruleset = RuleSet(scope=RuleScope.PROJECT)

        assert ruleset.scope == RuleScope.PROJECT
        assert len(ruleset.rules) == 0
        assert ruleset.metadata == {}


class TestRuleContextModel:
    def test_create_rule_context(self):
        context = RuleContext(
            user_id="user123",
            project_id="proj456",
            session_id="sess789",
            model_name="gpt-4",
            prompt_length=1500,
            custom_attributes={"environment": "production", "user_role": "admin"},
        )

        assert context.user_id == "user123"
        assert context.project_id == "proj456"
        assert context.model_name == "gpt-4"
        assert context.prompt_length == 1500
        assert context.custom_attributes["environment"] == "production"

    def test_minimal_context(self):
        context = RuleContext()

        assert context.user_id is None
        assert context.custom_attributes == {}


class TestRuleEvaluationResult:
    def test_create_evaluation_result(self):
        result = RuleEvaluationResult(
            rule_name="test_rule",
            action=RuleAction.ALLOW,
            matched=True,
            parameters={"message": "Allowed"},
            priority=50,
            execution_time_ms=15.5,
        )

        assert result.rule_name == "test_rule"
        assert result.action == RuleAction.ALLOW
        assert result.matched is True
        assert result.parameters == {"message": "Allowed"}
        assert result.priority == 50
        assert result.execution_time_ms == 15.5


class TestRuleEvaluationSummary:
    def test_create_evaluation_summary(self):
        context = RuleContext(user_id="test_user")
        results = [
            RuleEvaluationResult(
                rule_name="rule1", action=RuleAction.ALLOW, matched=True, priority=50
            )
        ]

        summary = RuleEvaluationSummary(
            context=context,
            results=results,
            final_action=RuleAction.ALLOW,
            total_execution_time_ms=25.7,
            evaluated_at=datetime.utcnow().isoformat(),
            applicable_rules_count=3,
            matched_rules_count=1,
        )

        assert summary.context.user_id == "test_user"
        assert len(summary.results) == 1
        assert summary.final_action == RuleAction.ALLOW
        assert summary.applicable_rules_count == 3
        assert summary.matched_rules_count == 1


class TestEnums:
    def test_rule_scope_enum(self):
        assert RuleScope.GLOBAL == "global"
        assert RuleScope.PROJECT == "project"
        assert RuleScope.INDIVIDUAL == "individual"

    def test_rule_action_enum(self):
        assert RuleAction.ALLOW == "allow"
        assert RuleAction.DENY == "deny"
        assert RuleAction.WARN == "warn"
        assert RuleAction.MODIFY == "modify"
        assert RuleAction.VALIDATE == "validate"

    def test_priority_tie_breaking_enum(self):
        assert PriorityTieBreaking.FIFO == "fifo"
        assert PriorityTieBreaking.LEXICOGRAPHIC == "lexi"
        assert PriorityTieBreaking.FIRST_WINS == "first"
