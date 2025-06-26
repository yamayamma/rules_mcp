#!/usr/bin/env python3
"""Debug MCP Server

Debug the FastMCP tool registration process.
"""

# ruff: noqa: E402

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastmcp import FastMCP

from rule_manager.models.settings import ServerSettings
from rule_manager.server import RuleManagerServer


async def debug_fastmcp_registration():
    """Debug FastMCP tool registration"""

    print("🔍 Debugging FastMCP Tool Registration...")

    # Test 1: Simple FastMCP with tools
    print("\n1️⃣ Testing simple FastMCP...")

    simple_mcp = FastMCP("Simple Test")

    @simple_mcp.tool()
    def simple_tool() -> str:
        """A simple test tool"""
        return "Hello from simple tool!"

    # Check if tool is registered
    print(
        f"   📋 Simple MCP dir: {[attr for attr in dir(simple_mcp) if 'tool' in attr.lower()]}"
    )

    # Try get_tools method
    try:
        tools = await simple_mcp.get_tools()
        tool_names = [tool.name for tool in tools]
        print(f"   ✅ Simple get_tools(): {tool_names}")
    except Exception as e:
        print(f"   ❌ get_tools() failed: {e}")
        tool_names = []

    if hasattr(simple_mcp, "tools"):
        print(f"   ✅ Simple tools: {list(simple_mcp.tools.keys())}")
    elif hasattr(simple_mcp, "_tools"):
        print(f"   ✅ Simple _tools: {list(simple_mcp._tools.keys())}")
    else:
        print("   ❌ No tools found in simple MCP")

    # Test 2: Our RuleManagerServer
    print("\n2️⃣ Testing RuleManagerServer...")

    settings = ServerSettings(rules_dir="config/rules")
    server = RuleManagerServer(settings)

    print(
        f"   📋 Server MCP dir: {[attr for attr in dir(server.mcp) if 'tool' in attr.lower()]}"
    )

    # Try get_tools method for server
    try:
        tools = await server.mcp.get_tools()
        tool_names = [tool.name for tool in tools]
        print(f"   ✅ Server get_tools(): {tool_names}")

        # Show tool details
        for tool in tools[:3]:  # First 3 tools
            print(
                f"      🔧 {tool.name}: {getattr(tool, 'description', 'No description')}"
            )

    except Exception as e:
        print(f"   ❌ Server get_tools() failed: {e}")
        tool_names = []
        tools = []

    # Try different ways to access tools
    tools_found = False

    if hasattr(server.mcp, "tools"):
        tools = server.mcp.tools
        print(f"   ✅ Server tools: {list(tools.keys()) if tools else 'Empty'}")
        tools_found = True

    if hasattr(server.mcp, "_tools"):
        tools = server.mcp._tools
        print(f"   ✅ Server _tools: {list(tools.keys()) if tools else 'Empty'}")
        tools_found = True

    if not tools_found:
        print("   ❌ No tools found in server MCP")

    # Test 3: Check if tools were registered but not shown properly
    print("\n3️⃣ Testing tool calls...")

    if tool_names:  # If we found tools
        try:
            # Try to call health_check if it exists
            if "health_check" in tool_names:
                health_tool = None
                for tool in tools:
                    if tool.name == "health_check":
                        health_tool = tool
                        break

                if health_tool:
                    print("   🔧 Testing health_check tool...")
                    # We can't call it directly here, but we know it exists
                    print("   ✅ health_check tool found and ready")

        except Exception as e:
            print(f"   ❌ Tool call test failed: {e}")


async def debug_server_internals():
    """Debug server internal state"""

    print("\n🔍 Debugging Server Internals...")

    settings = ServerSettings(rules_dir="config/rules")
    server = RuleManagerServer(settings)

    print(f"   📋 Server settings: {settings.transport}")
    print(f"   📋 Rule store: {type(server.rule_store).__name__}")
    print(f"   📋 Rule engine: {type(server.rule_engine).__name__}")
    print(f"   📋 MCP instance: {type(server.mcp).__name__}")

    # Check MCP state
    mcp_attrs = [attr for attr in dir(server.mcp) if not attr.startswith("__")]
    print(f"   📋 MCP attributes: {mcp_attrs[:15]}")  # First 15

    # Try to manually call _register_tools again
    print("\n   🔧 Re-calling _register_tools...")
    try:
        server._register_tools()
        print("   ✅ _register_tools completed")
    except Exception as e:
        print(f"   ❌ _register_tools failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main debug function"""

    print("🐛 FastMCP Debug Session")
    print("=" * 30)

    await debug_fastmcp_registration()
    await debug_server_internals()

    print("\n" + "=" * 30)
    print("✅ Debug session completed!")


if __name__ == "__main__":
    asyncio.run(main())
