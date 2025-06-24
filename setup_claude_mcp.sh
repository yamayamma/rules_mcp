#!/bin/bash

# Setup script for configuring rules_mcp with Claude Code

set -e

echo "🚀 Setting up rules_mcp for Claude Code..."

# Get the absolute path to the rules_mcp directory
RULES_MCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Rules MCP directory: $RULES_MCP_DIR"

# Check if virtual environment exists
if [ ! -d "$RULES_MCP_DIR/venv" ]; then
    echo "❌ Virtual environment not found. Please run the main setup script first."
    exit 1
fi

# Check if dependencies are installed
if ! bash -c "cd '$RULES_MCP_DIR' && source venv/bin/activate && PYTHONPATH=src python -c 'import rule_manager'" 2>/dev/null; then
    echo "❌ Dependencies not properly installed. Please run the main setup script first."
    exit 1
fi

# Test the MCP server
echo "🧪 Testing MCP server..."
if timeout 3s bash -c "cd '$RULES_MCP_DIR' && source venv/bin/activate && PYTHONPATH=src python -m rule_manager.main --help" >/dev/null 2>&1; then
    echo "✅ MCP server test passed"
else
    echo "❌ MCP server test failed"
    exit 1
fi

# Create MCP configuration for Claude Code
MCP_CONFIG_FILE="$RULES_MCP_DIR/claude_mcp_config.json"
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "rules_mcp": {
      "command": "$RULES_MCP_DIR/venv/bin/python",
      "args": ["-m", "rule_manager.main"],
      "cwd": "$RULES_MCP_DIR",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
EOF

echo "✅ Created MCP configuration: $MCP_CONFIG_FILE"

echo ""
echo "🎉 Setup completed!"
echo ""
echo "To configure Claude Code with this MCP server:"
echo "1. Copy the configuration from: $MCP_CONFIG_FILE"
echo "2. Add it to your Claude Code MCP settings"
echo ""
echo "Or manually configure with these details:"
echo "  Server Name: rules_mcp"
echo "  Command: $RULES_MCP_DIR/venv/bin/python"
echo "  Args: ['-m', 'rule_manager.main']"
echo "  Working Directory: $RULES_MCP_DIR"
echo "  Environment: PYTHONPATH=src"
echo ""
echo "The server provides these MCP tools:"
echo "  - evaluate_rules: Evaluate rules against a context"
echo "  - create_rule: Create a new rule"
echo "  - update_rule: Update an existing rule"
echo "  - delete_rule: Delete a rule"
echo "  - list_rules: List all rules"
echo "  - get_rule: Get a specific rule"
echo "  - validate_rule_dsl: Validate DSL expressions"
echo "  - health_check: Check server health"