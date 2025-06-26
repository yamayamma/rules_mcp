import time
from datetime import datetime
from typing import Any

import semver

from ..models.base import (
    PriorityTieBreaking,
    Rule,
    RuleAction,
    RuleContext,
    RuleEvaluationResult,
    RuleEvaluationSummary,
    RuleScope,
    RuleSet,
)
from ..models.errors import (
    CircularInheritanceError,
    InvalidRulesetVersionError,
    UnexpectedError,
)
from ..storage.base import RuleStore
from .dsl import DSLEvaluator


class RuleEngine:
    def __init__(
        self,
        rule_store: RuleStore,
        priority_tie_breaking: PriorityTieBreaking = PriorityTieBreaking.FIFO,
        max_evaluation_time_ms: int = 1000,
        engine_version: str = "2.8.0",
    ):
        self.rule_store = rule_store
        self.priority_tie_breaking = priority_tie_breaking
        self.max_evaluation_time_ms = max_evaluation_time_ms
        self.engine_version = engine_version
        self.dsl_evaluator = DSLEvaluator()
        self._rule_cache: dict[RuleScope, RuleSet] = {}
        self._inheritance_cache: dict[str, Rule] = {}

    async def evaluate_rules(self, context: RuleContext) -> RuleEvaluationSummary:
        """
        Evaluate all applicable rules against the given context.
        """
        start_time = time.time()

        try:
            # Load all applicable rules
            applicable_rules = await self._get_applicable_rules(context)

            # Evaluate each rule
            results = []
            for rule in applicable_rules:
                result = await self._evaluate_rule(rule, context)
                results.append(result)

            # Determine final action
            final_action = self._determine_final_action(results)

            execution_time = (time.time() - start_time) * 1000

            return RuleEvaluationSummary(
                context=context,
                results=results,
                final_action=final_action,
                total_execution_time_ms=execution_time,
                evaluated_at=datetime.utcnow().isoformat(),
                applicable_rules_count=len(applicable_rules),
                matched_rules_count=sum(1 for r in results if r.matched),
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            raise UnexpectedError(
                f"Rule evaluation failed after {execution_time:.2f}ms: {e}"
            ) from e

    async def _get_applicable_rules(self, context: RuleContext) -> list[Rule]:
        """
        Get all rules that should be evaluated for the given context.
        Rules are ordered by scope hierarchy and priority.
        """
        all_rules = []

        # Load rules from all scopes in hierarchy order
        for scope in [RuleScope.GLOBAL, RuleScope.PROJECT, RuleScope.INDIVIDUAL]:
            ruleset = await self.rule_store.load_rules(scope)

            # Validate ruleset version
            self._validate_ruleset_version(ruleset)

            # Add enabled rules
            scope_rules = [rule for rule in ruleset.rules if rule.enabled]
            all_rules.extend(scope_rules)

        # Resolve inheritance
        resolved_rules = await self._resolve_inheritance(all_rules)

        # Sort by priority and tie-breaking
        return self._sort_rules_by_priority(resolved_rules)

    async def _evaluate_rule(
        self, rule: Rule, context: RuleContext
    ) -> RuleEvaluationResult:
        """
        Evaluate a single rule against the context.
        """
        start_time = time.time()

        try:
            # Check if rule conditions match
            matched = True
            if rule.conditions:
                for _condition_name, condition_expr in rule.conditions.items():
                    if isinstance(condition_expr, str):
                        condition_matched = self.dsl_evaluator.evaluate(
                            condition_expr, context
                        )
                        if not condition_matched:
                            matched = False
                            break
                    elif isinstance(condition_expr, dict):
                        # Handle complex condition objects
                        matched = self._evaluate_complex_condition(
                            condition_expr, context
                        )
                        if not matched:
                            break

            execution_time = (time.time() - start_time) * 1000

            return RuleEvaluationResult(
                rule_name=rule.name,
                action=rule.action,
                matched=matched,
                parameters=rule.parameters.copy() if matched else {},
                message=self._generate_rule_message(rule, matched),
                priority=rule.priority,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return RuleEvaluationResult(
                rule_name=rule.name,
                action=RuleAction.DENY,
                matched=False,
                parameters={},
                message=f"Rule evaluation error: {e}",
                priority=rule.priority,
                execution_time_ms=execution_time,
            )

    def _evaluate_complex_condition(
        self, condition: dict[str, Any], context: RuleContext
    ) -> bool:
        """
        Evaluate complex condition objects.
        """
        # Handle logical operators
        if "and" in condition:
            return all(
                self._evaluate_condition_item(item, context)
                for item in condition["and"]
            )
        elif "or" in condition:
            return any(
                self._evaluate_condition_item(item, context) for item in condition["or"]
            )
        elif "not" in condition:
            return not self._evaluate_condition_item(condition["not"], context)
        else:
            return self._evaluate_condition_item(condition, context)

    def _evaluate_condition_item(self, item: Any, context: RuleContext) -> bool:
        """
        Evaluate a single condition item.
        """
        if isinstance(item, str):
            return self.dsl_evaluator.evaluate(item, context)
        elif isinstance(item, dict):
            return self._evaluate_complex_condition(item, context)
        else:
            return bool(item)

    async def _resolve_inheritance(self, rules: list[Rule]) -> list[Rule]:
        """
        Resolve rule inheritance and detect circular dependencies.
        """
        rule_map = {rule.name: rule for rule in rules}
        resolved_rules = []
        visited = set()

        for rule in rules:
            if rule.name not in visited:
                resolved_rule = await self._resolve_rule_inheritance(
                    rule, rule_map, set()
                )
                resolved_rules.append(resolved_rule)
                visited.add(rule.name)

        return resolved_rules

    async def _resolve_rule_inheritance(
        self, rule: Rule, rule_map: dict[str, Rule], current_path: set[str]
    ) -> Rule:
        """
        Resolve inheritance for a single rule.
        """
        if rule.name in current_path:
            chain = " -> ".join(current_path) + f" -> {rule.name}"
            raise CircularInheritanceError(chain)

        if not rule.inherits_from and not rule.parent_rule:
            return rule

        current_path.add(rule.name)
        resolved_rule = rule.model_copy(deep=True)

        # Handle parent_rule (single inheritance)
        if rule.parent_rule and rule.parent_rule in rule_map:
            parent = await self._resolve_rule_inheritance(
                rule_map[rule.parent_rule], rule_map, current_path
            )
            resolved_rule = self._merge_rules(parent, resolved_rule)

        # Handle inherits_from (multiple inheritance)
        if rule.inherits_from:
            for inherited_rule_name in rule.inherits_from:
                if inherited_rule_name in rule_map:
                    inherited_rule = await self._resolve_rule_inheritance(
                        rule_map[inherited_rule_name], rule_map, current_path
                    )
                    resolved_rule = self._merge_rules(inherited_rule, resolved_rule)

        current_path.remove(rule.name)
        return resolved_rule

    def _merge_rules(self, base_rule: Rule, derived_rule: Rule) -> Rule:
        """
        Merge a derived rule with its base rule.
        Derived rule takes precedence.
        """
        merged = base_rule.model_copy(deep=True)

        # Override with derived rule values
        if derived_rule.name:
            merged.name = derived_rule.name
        if derived_rule.scope:
            merged.scope = derived_rule.scope
        if derived_rule.priority != 50:  # 50 is default
            merged.priority = derived_rule.priority
        if derived_rule.action:
            merged.action = derived_rule.action
        if derived_rule.description:
            merged.description = derived_rule.description

        # Merge conditions and parameters
        merged.conditions.update(derived_rule.conditions)
        merged.parameters.update(derived_rule.parameters)

        return merged

    def _sort_rules_by_priority(self, rules: list[Rule]) -> list[Rule]:
        """
        Sort rules by priority and apply tie-breaking strategy.
        """

        def sort_key(rule: Rule):
            if self.priority_tie_breaking == PriorityTieBreaking.LEXICOGRAPHIC:
                return (-rule.priority, rule.name)
            elif self.priority_tie_breaking == PriorityTieBreaking.FIRST_WINS:
                return (-rule.priority, 0)  # Maintain original order for same priority
            else:  # FIFO (default)
                return (-rule.priority,)

        return sorted(rules, key=sort_key)

    def _determine_final_action(
        self, results: list[RuleEvaluationResult]
    ) -> RuleAction:
        """
        Determine the final action based on rule evaluation results.
        """
        if not results:
            return RuleAction.ALLOW

        # Find highest priority matched rule
        matched_results = [r for r in results if r.matched]
        if not matched_results:
            return RuleAction.ALLOW

        # Sort by priority (highest first)
        matched_results.sort(key=lambda r: r.priority, reverse=True)

        # Handle priority conflicts
        highest_priority = matched_results[0].priority
        highest_priority_results = [
            r for r in matched_results if r.priority == highest_priority
        ]

        if len(highest_priority_results) > 1:
            if self.priority_tie_breaking == PriorityTieBreaking.FIRST_WINS:
                return highest_priority_results[0].action
            elif self.priority_tie_breaking == PriorityTieBreaking.LEXICOGRAPHIC:
                highest_priority_results.sort(key=lambda r: r.rule_name)
                return highest_priority_results[0].action
            else:  # FIFO
                return highest_priority_results[0].action

        return matched_results[0].action

    def _generate_rule_message(self, rule: Rule, matched: bool) -> str:
        """
        Generate a descriptive message for the rule evaluation result.
        """
        status = "matched" if matched else "not matched"
        message = f"Rule '{rule.name}' {status}"

        if rule.description:
            message += f": {rule.description}"

        return message

    def _validate_ruleset_version(self, ruleset: RuleSet) -> None:
        """
        Validate that the ruleset version is compatible with this engine.
        """
        if not ruleset.engine_min_version:
            return

        try:
            min_version = ruleset.engine_min_version.replace(">=", "").strip()
            if not semver.compare(self.engine_version, min_version) >= 0:
                raise InvalidRulesetVersionError(ruleset.ruleset_version, min_version)
        except Exception as e:
            if isinstance(e, InvalidRulesetVersionError):
                raise
            # If semver parsing fails, just log and continue
