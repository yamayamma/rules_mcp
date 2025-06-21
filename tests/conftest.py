import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path

from rule_manager.storage.yaml_store import YAMLRuleStore
from rule_manager.models.base import Rule, RuleSet, RuleScope, RuleAction, RuleContext
from rule_manager.core.engine import RuleEngine


@pytest.fixture
def temp_rules_dir():
    """Create a temporary directory for test rules"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def yaml_store(temp_rules_dir):
    """Create a YAMLRuleStore instance for testing"""
    return YAMLRuleStore(temp_rules_dir)


@pytest.fixture
async def rule_engine(yaml_store):
    """Create a RuleEngine instance for testing"""
    return RuleEngine(yaml_store)


@pytest.fixture
def sample_rules():
    """Sample rules for testing"""
    return [
        Rule(
            name="allow_admins",
            scope=RuleScope.GLOBAL,
            priority=90,
            action=RuleAction.ALLOW,
            conditions={"role": "user_role == 'admin'"},
            description="Allow admin users"
        ),
        Rule(
            name="rate_limit",
            scope=RuleScope.GLOBAL,
            priority=80,
            action=RuleAction.DENY,
            conditions={"rate": "request_count > 100"},
            description="Rate limiting"
        ),
        Rule(
            name="default_allow",
            scope=RuleScope.GLOBAL,
            priority=10,
            action=RuleAction.ALLOW,
            conditions={},
            description="Default allow rule"
        )
    ]


@pytest.fixture
def sample_context():
    """Sample rule context for testing"""
    return RuleContext(
        user_id="test_user",
        project_id="test_project",
        model_name="gpt-4",
        prompt_length=1000,
        custom_attributes={
            "user_role": "admin",
            "request_count": 50,
            "environment": "test"
        }
    )


@pytest.fixture
async def populated_store(yaml_store, sample_rules):
    """A YAMLRuleStore populated with sample rules"""
    ruleset = RuleSet(scope=RuleScope.GLOBAL, rules=sample_rules)
    await yaml_store.save_rules(ruleset)
    return yaml_store


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()