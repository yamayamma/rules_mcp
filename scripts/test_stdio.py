#!/usr/bin/env python3
"""
Test MCP Server in STDIO mode

This script tests the MCP server by starting it and sending MCP messages
through stdin/stdout.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def test_mcp_stdio():
    """Test MCP server via STDIO"""

    print("🚀 Testing MCP Server via STDIO...")

    # Start the MCP server as a subprocess
    python_path = project_root / "venv" / "bin" / "python"
    if not python_path.exists():
        python_path = "python"

    server_process = await asyncio.create_subprocess_exec(
        str(python_path),
        "-m",
        "rule_manager.main",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(project_root),
    )

    print(f"   ✅ MCP Server started (PID: {server_process.pid})")

    try:
        # Test MCP initialization
        print("\n1️⃣ Testing MCP initialization...")

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        # Send initialization request
        request_json = json.dumps(init_request) + "\n"
        server_process.stdin.write(request_json.encode())
        await server_process.stdin.drain()

        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                server_process.stdout.readline(), timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.decode().strip())
                print(
                    f"   ✅ Initialization response: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}"
                )
            else:
                print("   ❌ No response from server")

        except asyncio.TimeoutError:
            print("   ❌ Initialization timeout")
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON response: {e}")

        # Test tools/list request
        print("\n2️⃣ Testing tools/list...")

        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        request_json = json.dumps(tools_request) + "\n"
        server_process.stdin.write(request_json.encode())
        await server_process.stdin.drain()

        try:
            response_line = await asyncio.wait_for(
                server_process.stdout.readline(), timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.decode().strip())
                tools = response.get("result", {}).get("tools", [])
                print(f"   ✅ Found {len(tools)} tools:")
                for tool in tools[:5]:  # Show first 5 tools
                    print(f"      📋 {tool.get('name', 'Unknown')}")
                if len(tools) > 5:
                    print(f"      ... and {len(tools) - 5} more tools")
            else:
                print("   ❌ No response to tools/list")

        except asyncio.TimeoutError:
            print("   ❌ Tools/list timeout")
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON response: {e}")

        # Test a specific tool call
        print("\n3️⃣ Testing health_check tool...")

        health_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "health_check", "arguments": {}},
        }

        request_json = json.dumps(health_request) + "\n"
        server_process.stdin.write(request_json.encode())
        await server_process.stdin.drain()

        try:
            response_line = await asyncio.wait_for(
                server_process.stdout.readline(), timeout=5.0
            )

            if response_line:
                response = json.loads(response_line.decode().strip())
                result = response.get("result", {})
                if "content" in result:
                    content = (
                        result["content"][0]["text"] if result["content"] else "{}"
                    )
                    health_data = json.loads(content)
                    print(
                        f"   ✅ Health check: {health_data.get('healthy', 'Unknown')}"
                    )
                else:
                    print(f"   📊 Health response: {result}")
            else:
                print("   ❌ No response to health_check")

        except asyncio.TimeoutError:
            print("   ❌ Health check timeout")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"   ❌ Error parsing health response: {e}")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        try:
            await asyncio.wait_for(server_process.wait(), timeout=3.0)
            print("   ✅ Server terminated gracefully")
        except asyncio.TimeoutError:
            server_process.kill()
            await server_process.wait()
            print("   ⚠️ Server force-killed")


async def test_mcp_with_mock_client():
    """Test with a simplified mock MCP client"""

    print("\n🤖 Testing with Mock MCP Client...")

    try:
        # Import and run server directly
        from rule_manager.models.settings import ServerSettings
        from rule_manager.server import RuleManagerServer

        settings = ServerSettings(transport="stdio", rules_dir="config/rules")

        server = RuleManagerServer(settings)

        print("   ✅ Server initialized")
        print(f"   📋 Server has MCP instance: {hasattr(server, 'mcp')}")

        # Check if server has tools registered
        if hasattr(server.mcp, "_tools"):
            tools = list(server.mcp._tools.keys())
            print(f"   📋 Registered tools: {tools}")
        else:
            print("   ⚠️ No tools attribute found on MCP instance")

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function"""

    print("🧪 MCP STDIO Test Suite")
    print("=" * 40)

    # First test with mock client
    await test_mcp_with_mock_client()

    # Then test actual STDIO communication
    await test_mcp_stdio()

    print("\n" + "=" * 40)
    print("✅ STDIO tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
