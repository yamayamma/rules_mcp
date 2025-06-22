#!/usr/bin/env python3
"""
Minimal MCP Server Test

Test basic FastMCP functionality to understand the API.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastmcp import FastMCP


async def test_minimal_mcp():
    """Test minimal FastMCP setup"""

    print("🧪 Testing Minimal FastMCP Setup...")

    # Create a minimal MCP server
    mcp = FastMCP("Test Server")

    # Add a simple tool
    @mcp.tool()
    def hello_world(name: str = "World") -> str:
        """Say hello to someone"""
        return f"Hello, {name}!"

    @mcp.tool()
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    print("   ✅ MCP server created")
    print(f"   📋 Server name: {getattr(mcp, 'name', 'Unknown')}")

    # Check if tools are registered
    if hasattr(mcp, "_tools"):
        tools = list(mcp._tools.keys())
        print(f"   📋 Registered tools: {tools}")
    elif hasattr(mcp, "tools"):
        print(f"   📋 Tools attribute found")
    else:
        print("   ⚠️ No tools attribute found")

    # Check available attributes
    attrs = [attr for attr in dir(mcp) if not attr.startswith("_")]
    print(f"   📋 Available methods: {attrs[:10]}")  # Show first 10

    # Try to get tools info
    try:
        # Different ways FastMCP might expose tools
        if hasattr(mcp, "get_tools"):
            tools_info = await mcp.get_tools()
            print(f"   📋 Tools info: {tools_info}")
        elif hasattr(mcp, "list_tools"):
            tools_info = await mcp.list_tools()
            print(f"   📋 Tools info: {tools_info}")
        else:
            print("   ⚠️ No method to list tools found")
    except Exception as e:
        print(f"   ⚠️ Error getting tools: {e}")

    return mcp


async def test_fastmcp_run():
    """Test FastMCP run method"""

    print("\n🚀 Testing FastMCP Run...")

    mcp = FastMCP("Test Server")

    @mcp.tool()
    def test_tool() -> str:
        """A test tool"""
        return "test result"

    # Check run method signature
    if hasattr(mcp, "run"):
        import inspect

        sig = inspect.signature(mcp.run)
        print(f"   📋 Run method signature: {sig}")

        # Try to understand what parameters run() accepts
        params = list(sig.parameters.keys())
        print(f"   📋 Run parameters: {params}")
    else:
        print("   ❌ No run method found")


async def main():
    """Main test function"""

    print("🔬 FastMCP API Exploration")
    print("=" * 30)

    mcp = await test_minimal_mcp()
    await test_fastmcp_run()

    print("\n" + "=" * 30)
    print("✅ FastMCP exploration completed!")


if __name__ == "__main__":
    asyncio.run(main())
