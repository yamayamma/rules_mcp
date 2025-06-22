#!/usr/bin/env python3
"""
Test Working MCP Server

Test the rule manager MCP server using the correct FastMCP API.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from rule_manager.models.base import RuleContext, RuleScope, RuleAction
from rule_manager.models.settings import ServerSettings
from rule_manager.server import RuleManagerServer


async def test_server_tools():
    """Test server tools directly"""

    print("🧪 Testing Server Tools Directly...")

    # Create server instance
    settings = ServerSettings(
        transport="stdio", rules_dir="config/rules", storage_backend="yaml"
    )

    server = RuleManagerServer(settings)

    print(f"   ✅ Server created: {server.mcp.name}")

    # Get tools info from FastMCP (using the correct method)
    try:
        # Try different ways to access tools
        if hasattr(server.mcp, "tools"):
            tools_dict = server.mcp.tools
        elif hasattr(server.mcp, "_tools"):
            tools_dict = server.mcp._tools
        else:
            print("   ❌ No tools attribute found")
            return False

        tool_names = list(tools_dict.keys())
        print(f"   📋 Registered tools ({len(tool_names)}): {tool_names}")

        # Test each tool
        for tool_name, tool in tools_dict.items():
            print(
                f"   🔧 Tool: {tool_name} - {getattr(tool, 'description', 'No description')}"
            )

    except Exception as e:
        print(f"   ❌ Error accessing tools: {e}")
        return False

    # Test health_check tool specifically
    print("\n1️⃣ Testing health_check tool...")
    try:
        health_tool = tools_dict.get("health_check")
        if health_tool:
            # Call the tool function directly
            result = await health_tool.function()
            print(f"   ✅ Health check result: {result}")
        else:
            print("   ❌ health_check tool not found")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")

    # Test evaluate_rules tool
    print("\n2️⃣ Testing evaluate_rules tool...")
    try:
        eval_tool = tools_dict.get("evaluate_rules")
        if eval_tool:
            # Create test request
            from rule_manager.server import EvaluateRulesRequest

            test_context = RuleContext(
                user_id="test_user",
                model_name="gpt-4",
                prompt_length=1500,
                custom_attributes={
                    "user_role": "admin",
                    "environment": "test",
                    "request_count_per_minute": 50,
                },
            )

            request = EvaluateRulesRequest(context=test_context)
            result = await eval_tool.function(request)

            print(f"   ✅ Evaluation result:")
            print(f"      📊 Final action: {result.get('final_action')}")
            print(f"      📊 Matched rules: {result.get('matched_rules_count')}")
            print(f"      ⏱️ Time: {result.get('total_execution_time_ms'):.2f}ms")
        else:
            print("   ❌ evaluate_rules tool not found")
    except Exception as e:
        print(f"   ❌ Evaluation failed: {e}")
        import traceback

        traceback.print_exc()

    # Test list_rules tool
    print("\n3️⃣ Testing list_rules tool...")
    try:
        list_tool = tools_dict.get("list_rules")
        if list_tool:
            result = await list_tool.function()

            if result.get("success"):
                rules_count = result.get("count", 0)
                print(f"   ✅ Listed {rules_count} rules")

                if rules_count > 0:
                    rules = result.get("rules", [])
                    for rule in rules[:3]:  # Show first 3
                        print(
                            f"      📋 {rule['name']} ({rule['scope']}) - {rule['action']}"
                        )
            else:
                print(f"   ❌ List rules failed: {result}")
        else:
            print("   ❌ list_rules tool not found")
    except Exception as e:
        print(f"   ❌ List rules failed: {e}")

    # Test validate_rule_dsl tool
    print("\n4️⃣ Testing validate_rule_dsl tool...")
    try:
        validate_tool = tools_dict.get("validate_rule_dsl")
        if validate_tool:
            # Test valid expression
            result = await validate_tool.function(
                "user_id == 'test' and prompt_length > 1000"
            )
            print(f"   ✅ DSL validation result: {result}")
        else:
            print("   ❌ validate_rule_dsl tool not found")
    except Exception as e:
        print(f"   ❌ DSL validation failed: {e}")

    return True


async def test_mcp_server_startup():
    """Test MCP server startup process"""

    print("\n🚀 Testing MCP Server Startup...")

    settings = ServerSettings(transport="stdio", rules_dir="config/rules")

    server = RuleManagerServer(settings)

    print(f"   ✅ Server initialized")
    print(f"   📋 Transport: {settings.transport}")
    print(f"   📋 Rules dir: {settings.rules_dir}")
    print(f"   📋 Storage: {settings.storage_backend}")

    # Check if we can call run method (but don't actually run it)
    try:
        import inspect

        run_sig = inspect.signature(server.run)
        print(f"   📋 Run method signature: {run_sig}")
        print("   ✅ Server ready to run")
    except Exception as e:
        print(f"   ❌ Run method issue: {e}")


async def main():
    """Main test function"""

    print("🎯 Rule Manager MCP Server Test")
    print("=" * 40)

    try:
        # Test server tools directly
        tools_success = await test_server_tools()

        if tools_success:
            # Test server startup
            await test_mcp_server_startup()

        print("\n" + "=" * 40)
        print("✅ All MCP server tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
