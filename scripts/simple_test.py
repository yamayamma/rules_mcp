#!/usr/bin/env python3
"""
Simple MCP Server Test

Test the MCP server by directly calling the tools without going through
the MCP protocol.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from rule_manager.models.base import RuleContext, RuleScope, RuleAction
from rule_manager.models.settings import ServerSettings
from rule_manager.core.engine import RuleEngine
from rule_manager.storage.yaml_store import YAMLRuleStore


async def test_rule_engine_directly():
    """Test the rule engine directly without MCP"""

    print("🧪 Testing Rule Engine Directly...")

    # Initialize components
    settings = ServerSettings(
        rules_dir="config/rules", storage_backend="yaml", log_level="INFO"
    )

    store = YAMLRuleStore(settings.rules_dir)
    engine = RuleEngine(
        rule_store=store,
        priority_tie_breaking=settings.priority_tie_breaking,
        max_evaluation_time_ms=settings.max_evaluation_time_ms,
    )

    # Test 1: Health Check (Storage)
    print("\n1️⃣ Testing storage health check...")
    try:
        healthy = await store.health_check()
        print(f"   ✅ Storage health: {healthy}")
    except Exception as e:
        print(f"   ❌ Storage health check failed: {e}")
        return False

    # Test 2: Load Rules
    print("\n2️⃣ Testing rule loading...")
    try:
        global_rules = await store.load_rules(RuleScope.GLOBAL)
        print(f"   ✅ Loaded {len(global_rules.rules)} global rules")

        if global_rules.rules:
            first_rule = global_rules.rules[0]
            print(
                f"   📋 First rule: {first_rule.name} (priority: {first_rule.priority})"
            )
    except Exception as e:
        print(f"   ❌ Rule loading failed: {e}")
        return False

    # Test 3: Rule Evaluation
    print("\n3️⃣ Testing rule evaluation...")
    try:
        test_context = RuleContext(
            user_id="test_user_123",
            project_id="test_project",
            model_name="gpt-4",
            prompt_length=1500,
            custom_attributes={
                "user_role": "admin",
                "environment": "test",
                "request_count_per_minute": 50,
                "user_clearance_level": 5,
                "available_models": ["gpt-4", "gpt-3.5-turbo", "claude"],
                "contains_harmful_content": False,
                "user_daily_limit": 1000,
                "daily_request_count": 100,
            },
        )

        result = await engine.evaluate_rules(test_context)

        print(f"   ✅ Evaluation successful:")
        print(f"   📊 Final action: {result.final_action}")
        print(
            f"   📊 Matched rules: {result.matched_rules_count}/{result.applicable_rules_count}"
        )
        print(f"   ⏱️ Execution time: {result.total_execution_time_ms:.2f}ms")

        # Show matched rules
        matched_count = 0
        for rule_result in result.results:
            if rule_result.matched:
                matched_count += 1
                if matched_count <= 3:  # Show first 3 matches
                    print(
                        f"   🎯 {rule_result.rule_name}: {rule_result.action} (priority: {rule_result.priority})"
                    )

        if matched_count > 3:
            print(f"   📋 ... and {matched_count - 3} more matched rules")

    except Exception as e:
        print(f"   ❌ Rule evaluation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 4: DSL Validation
    print("\n4️⃣ Testing DSL validation...")
    try:
        # Test valid expressions
        valid_expressions = [
            "user_id == 'test'",
            "prompt_length > 1000",
            "user_role == 'admin' and environment == 'production'",
            "model_name in available_models",
        ]

        for expr in valid_expressions:
            issues = engine.dsl_evaluator.validate_expression(expr)
            if not issues:
                print(f"   ✅ Valid: {expr}")
            else:
                print(f"   ❌ Invalid: {expr} - {issues}")

        # Test invalid expression
        invalid_expr = "user_id == 'test' and ("
        issues = engine.dsl_evaluator.validate_expression(invalid_expr)
        if issues:
            print(f"   ✅ Correctly detected invalid: {invalid_expr}")
        else:
            print(f"   ❌ Failed to detect invalid: {invalid_expr}")

    except Exception as e:
        print(f"   ❌ DSL validation failed: {e}")

    print("\n🎉 Direct Testing Completed!")
    return True


async def test_different_scenarios():
    """Test different evaluation scenarios"""

    print("\n🎯 Testing Different Scenarios...")

    store = YAMLRuleStore("config/rules")
    engine = RuleEngine(rule_store=store)

    scenarios = [
        {
            "name": "Admin User in Production",
            "context": RuleContext(
                user_id="admin_001",
                custom_attributes={
                    "user_role": "admin",
                    "environment": "production",
                    "user_clearance_level": 5,
                    "request_count_per_minute": 25,
                },
            ),
        },
        {
            "name": "Regular User with High Usage",
            "context": RuleContext(
                user_id="user_456",
                prompt_length=3500,
                custom_attributes={
                    "user_role": "user",
                    "environment": "production",
                    "request_count_per_minute": 120,  # Over limit
                },
            ),
        },
        {
            "name": "Development Environment User",
            "context": RuleContext(
                user_id="dev_user",
                project_id="dev_project",
                custom_attributes={
                    "environment": "development",
                    "user_role": "developer",
                    "project_cost_tier": "budget",
                },
            ),
        },
        {
            "name": "Restricted Project Access",
            "context": RuleContext(
                user_id="contractor_001",
                project_id="classified",
                custom_attributes={
                    "user_clearance_level": 2,  # Low clearance
                    "user_role": "contractor",
                },
            ),
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}️⃣ Scenario: {scenario['name']}")
        try:
            result = await engine.evaluate_rules(scenario["context"])

            action = result.final_action
            matched = result.matched_rules_count
            time_ms = result.total_execution_time_ms

            print(f"   📊 Result: {action}")
            print(f"   📊 Matched: {matched} rules")
            print(f"   ⏱️ Time: {time_ms:.2f}ms")

            # Show key matched rules
            key_matches = []
            for rule_result in result.results:
                if rule_result.matched and rule_result.action != RuleAction.ALLOW:
                    key_matches.append(f"{rule_result.rule_name}({rule_result.action})")

            if key_matches:
                print(f"   🔍 Key matches: {', '.join(key_matches[:3])}")

        except Exception as e:
            print(f"   ❌ Scenario failed: {e}")

    print("\n🎉 Scenario Testing Completed!")


async def main():
    """Main test function"""

    print("🚀 LLM Rule Manager - Direct Engine Test")
    print("=" * 50)

    try:
        # Test rule engine directly
        engine_success = await test_rule_engine_directly()

        if engine_success:
            # Test different scenarios
            await test_different_scenarios()

        print("\n" + "=" * 50)
        print("✅ All direct tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
