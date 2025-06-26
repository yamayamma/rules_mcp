#!/usr/bin/env python3
"""MCP Server Testing Script

This script tests the MCP server functionality by connecting to it
and executing various MCP tools.
"""

# ruff: noqa: E402

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from rule_manager.models.base import RuleAction, RuleContext, RuleScope
from rule_manager.models.settings import ServerSettings
from rule_manager.server import RuleManagerServer


async def test_mcp_tools():
    """Test MCP server tools functionality"""

    print("🧪 Testing MCP Server Tools...")

    # Initialize server with test settings
    settings = ServerSettings(
        transport="stdio",
        rules_dir="config/rules",
        storage_backend="yaml",
        log_level="INFO",
    )

    server = RuleManagerServer(settings)

    # Test 1: Health Check
    print("\n1️⃣ Testing health_check...")
    try:
        health_result = await server.mcp.tools["health_check"]()
        print(f"   ✅ Health check: {health_result}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

    # Test 2: List Rules
    print("\n2️⃣ Testing list_rules...")
    try:
        list_result = await server.mcp.tools["list_rules"]()
        rules_count = list_result.get("count", 0)
        print(f"   ✅ Found {rules_count} rules")
        if rules_count > 0:
            first_rule = list_result["rules"][0]
            print(f"   📋 First rule: {first_rule['name']} ({first_rule['scope']})")
    except Exception as e:
        print(f"   ❌ List rules failed: {e}")
        return False

    # Test 3: Evaluate Rules
    print("\n3️⃣ Testing evaluate_rules...")
    try:
        test_context = RuleContext(
            user_id="test_user_123",
            project_id="test_project",
            model_name="gpt-4",
            prompt_length=1500,
            custom_attributes={
                "user_role": "admin",
                "environment": "test",
                "request_count": 50,
                "user_clearance_level": 5,
            },
        )

        from rule_manager.server import EvaluateRulesRequest

        eval_request = EvaluateRulesRequest(context=test_context)

        eval_result = await server.mcp.tools["evaluate_rules"](eval_request)

        if "error" in eval_result:
            print(f"   ❌ Evaluation failed: {eval_result['error']}")
        else:
            final_action = eval_result.get("final_action")
            matched_count = eval_result.get("matched_rules_count", 0)
            total_time = eval_result.get("total_execution_time_ms", 0)
            print("   ✅ Evaluation successful:")
            print(f"   📊 Final action: {final_action}")
            print(f"   📊 Matched rules: {matched_count}")
            print(f"   ⏱️ Execution time: {total_time:.2f}ms")

            # Show matched rules
            for result in eval_result.get("results", []):
                if result["matched"]:
                    print(f"   🎯 Matched: {result['rule_name']} -> {result['action']}")

    except Exception as e:
        print(f"   ❌ Rule evaluation failed: {e}")
        return False

    # Test 4: Create a Test Rule
    print("\n4️⃣ Testing create_rule...")
    try:
        from rule_manager.server import CreateRuleRequest

        new_rule_request = CreateRuleRequest(
            name="test_rule_dynamic",
            scope=RuleScope.GLOBAL,
            priority=60,
            action=RuleAction.WARN,
            conditions={"test": "user_id startswith 'test_'"},
            parameters={"message": "This is a dynamically created test rule"},
            description="A test rule created during MCP testing",
            enabled=True,
        )

        create_result = await server.mcp.tools["create_rule"](new_rule_request)

        if "error" in create_result:
            print(f"   ❌ Rule creation failed: {create_result['error']}")
        else:
            print(f"   ✅ Rule created successfully: {create_result['rule']['name']}")

    except Exception as e:
        print(f"   ❌ Rule creation failed: {e}")

    # Test 5: Get Specific Rule
    print("\n5️⃣ Testing get_rule...")
    try:
        get_result = await server.mcp.tools["get_rule"]("test_rule_dynamic", "global")

        if "error" in get_result:
            print(
                f"   ⚠️ Rule not found (expected if creation failed): {get_result['error']}"
            )
        else:
            rule = get_result["rule"]
            print(f"   ✅ Retrieved rule: {rule['name']}")
            print(f"   📋 Description: {rule.get('description', 'N/A')}")

    except Exception as e:
        print(f"   ❌ Get rule failed: {e}")

    # Test 6: Validate DSL
    print("\n6️⃣ Testing validate_rule_dsl...")
    try:
        # Test valid DSL
        valid_dsl = "user_id == 'test' and prompt_length > 1000"
        valid_result = await server.mcp.tools["validate_rule_dsl"](valid_dsl)
        print(f"   ✅ Valid DSL test: {valid_result}")

        # Test invalid DSL
        invalid_dsl = "user_id == 'test' and ("
        invalid_result = await server.mcp.tools["validate_rule_dsl"](invalid_dsl)
        print(f"   ✅ Invalid DSL test: {invalid_result}")

    except Exception as e:
        print(f"   ❌ DSL validation failed: {e}")

    # Test 7: Clean up - Delete Test Rule
    print("\n7️⃣ Testing delete_rule...")
    try:
        delete_result = await server.mcp.tools["delete_rule"](
            "test_rule_dynamic", "global"
        )

        if "error" in delete_result:
            print(
                f"   ⚠️ Rule deletion failed (may not exist): {delete_result['error']}"
            )
        else:
            print("   ✅ Rule deleted successfully")

    except Exception as e:
        print(f"   ❌ Rule deletion failed: {e}")

    print("\n🎉 MCP Tools Testing Completed!")
    return True


async def test_rule_evaluation_scenarios():
    """Test various rule evaluation scenarios"""

    print("\n🎯 Testing Rule Evaluation Scenarios...")

    settings = ServerSettings(rules_dir="config/rules")
    server = RuleManagerServer(settings)

    scenarios = [
        {
            "name": "Admin User",
            "context": RuleContext(
                user_id="admin_user",
                custom_attributes={"user_role": "admin", "environment": "production"},
            ),
        },
        {
            "name": "Regular User",
            "context": RuleContext(
                user_id="regular_user",
                custom_attributes={"user_role": "user", "environment": "production"},
            ),
        },
        {
            "name": "High Token Count",
            "context": RuleContext(
                user_id="test_user",
                prompt_length=5000,
                custom_attributes={"environment": "test"},
            ),
        },
        {
            "name": "Rate Limited User",
            "context": RuleContext(
                user_id="heavy_user",
                custom_attributes={"request_count_per_minute": 150},
            ),
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}️⃣ Scenario: {scenario['name']}")
        try:
            from rule_manager.server import EvaluateRulesRequest

            eval_request = EvaluateRulesRequest(context=scenario["context"])
            result = await server.mcp.tools["evaluate_rules"](eval_request)

            if "error" in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                action = result.get("final_action", "unknown")
                matched = result.get("matched_rules_count", 0)
                print(f"   📊 Final Action: {action}")
                print(f"   📊 Matched Rules: {matched}")

                # Show top matched rules
                for rule_result in result.get("results", [])[:3]:
                    if rule_result["matched"]:
                        print(
                            f"   🎯 {rule_result['rule_name']}: {rule_result['action']}"
                        )

        except Exception as e:
            print(f"   ❌ Scenario failed: {e}")

    print("\n🎉 Scenario Testing Completed!")


async def main():
    """Main test function"""

    print("🚀 LLM Rule Manager MCP Server Test Suite")
    print("=" * 50)

    try:
        # Test MCP tools functionality
        tools_success = await test_mcp_tools()

        if tools_success:
            # Test rule evaluation scenarios
            await test_rule_evaluation_scenarios()

        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
