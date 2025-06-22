#!/bin/bash

# LLM Rule Manager MCP Server Setup Script

set -e

echo "🚀 Setting up LLM Rule Manager MCP Server..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Python 3.11+ is required. Current version: $(python3 --version)"
    exit 1
fi

echo "✅ Python version check passed: $(python3 --version)"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p config/rules
mkdir -p logs
mkdir -p data

# Install dependencies
if command -v poetry &> /dev/null; then
    echo "📦 Installing dependencies with Poetry..."
    poetry install
    PYTHON_CMD="poetry run python"
else
    echo "📦 Installing dependencies with pip..."
    pip install -r requirements.txt
    PYTHON_CMD="python"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and modify as needed."
else
    echo "✅ .env file already exists"
fi

# Verify rule files exist
if [ ! -f config/rules/global.yaml ]; then
    echo "❌ Sample rule files not found in config/rules/"
    echo "Please ensure the rule files are present before running the server."
    exit 1
fi

echo "✅ Sample rule files found"

# Test basic functionality
echo "🧪 Testing basic functionality..."

# Test import
if $PYTHON_CMD -c "from rule_manager.main import main; print('✅ Import successful')" 2>/dev/null; then
    echo "✅ Module import successful"
else
    echo "❌ Module import failed"
    exit 1
fi

# Test YAML rule loading
if $PYTHON_CMD -c "
import asyncio
from rule_manager.storage.yaml_store import YAMLRuleStore
from rule_manager.models.base import RuleScope

async def test():
    store = YAMLRuleStore('config/rules')
    ruleset = await store.load_rules(RuleScope.GLOBAL)
    print(f'✅ Loaded {len(ruleset.rules)} rules from global.yaml')
    return len(ruleset.rules)

result = asyncio.run(test())
if result == 0:
    print('⚠️ Warning: No rules found in global.yaml')
" 2>/dev/null; then
    echo "✅ Rule loading test passed"
else
    echo "❌ Rule loading test failed"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the MCP server:"
echo "  STDIO mode:  $PYTHON_CMD -m rule_manager.main"
echo "  HTTP mode:   $PYTHON_CMD -m rule_manager.main --transport streamable-http --port 8080"
echo ""
echo "For more options: $PYTHON_CMD -m rule_manager.main --help"
echo ""
echo "📖 See docs/USAGE.md for detailed usage instructions"