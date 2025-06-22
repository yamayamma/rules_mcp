import pytest
import tempfile
import shutil
from pathlib import Path

from rule_manager.storage.yaml_store import YAMLRuleStore
from rule_manager.models.base import Rule, RuleSet, RuleScope, RuleAction
from rule_manager.models.errors import RuleNotFoundError


class TestYAMLRuleStore:
    def setup_method(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.store = YAMLRuleStore(self.temp_dir)

    def teardown_method(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    async def test_save_and_load_rules(self):
        # Create a test ruleset
        rules = [
            Rule(
                name="test_rule_1",
                scope=RuleScope.GLOBAL,
                action=RuleAction.ALLOW,
                priority=50,
                conditions={"user_id": "user_id == 'test'"},
            ),
            Rule(
                name="test_rule_2",
                scope=RuleScope.GLOBAL,
                action=RuleAction.DENY,
                priority=75,
                conditions={"model": "model_name == 'restricted'"},
            ),
        ]

        ruleset = RuleSet(
            scope=RuleScope.GLOBAL, rules=rules, metadata={"test": "data"}
        )

        # Save the ruleset
        await self.store.save_rules(ruleset)

        # Load the ruleset back
        loaded_ruleset = await self.store.load_rules(RuleScope.GLOBAL)

        assert loaded_ruleset.scope == RuleScope.GLOBAL
        assert len(loaded_ruleset.rules) == 2
        assert loaded_ruleset.metadata == {"test": "data"}

        # Check first rule
        rule1 = loaded_ruleset.rules[0]
        assert rule1.name == "test_rule_1"
        assert rule1.action == RuleAction.ALLOW
        assert rule1.priority == 50
        assert rule1.created_at is not None
        assert rule1.updated_at is not None

        # Check second rule
        rule2 = loaded_ruleset.rules[1]
        assert rule2.name == "test_rule_2"
        assert rule2.action == RuleAction.DENY
        assert rule2.priority == 75

    async def test_load_nonexistent_ruleset(self):
        # Loading a non-existent ruleset should return empty ruleset
        ruleset = await self.store.load_rules(RuleScope.PROJECT)

        assert ruleset.scope == RuleScope.PROJECT
        assert len(ruleset.rules) == 0

    async def test_add_rule(self):
        rule = Rule(
            name="new_rule",
            scope=RuleScope.GLOBAL,
            action=RuleAction.WARN,
            priority=60,
            description="A new test rule",
        )

        await self.store.add_rule(rule)

        # Verify rule was added
        loaded_ruleset = await self.store.load_rules(RuleScope.GLOBAL)
        assert len(loaded_ruleset.rules) == 1

        loaded_rule = loaded_ruleset.rules[0]
        assert loaded_rule.name == "new_rule"
        assert loaded_rule.action == RuleAction.WARN
        assert loaded_rule.description == "A new test rule"
        assert loaded_rule.created_at is not None

    async def test_add_duplicate_rule(self):
        rule = Rule(
            name="duplicate_rule", scope=RuleScope.GLOBAL, action=RuleAction.ALLOW
        )

        # Add rule first time - should succeed
        await self.store.add_rule(rule)

        # Add same rule again - should fail
        with pytest.raises(Exception):  # Should raise an error for duplicate
            await self.store.add_rule(rule)

    async def test_update_rule(self):
        # First add a rule
        original_rule = Rule(
            name="update_test",
            scope=RuleScope.GLOBAL,
            action=RuleAction.ALLOW,
            priority=50,
            description="Original description",
        )

        await self.store.add_rule(original_rule)

        # Update the rule
        updated_rule = Rule(
            name="update_test",
            scope=RuleScope.GLOBAL,
            action=RuleAction.DENY,
            priority=75,
            description="Updated description",
        )

        await self.store.update_rule(updated_rule)

        # Verify the update
        loaded_ruleset = await self.store.load_rules(RuleScope.GLOBAL)
        assert len(loaded_ruleset.rules) == 1

        rule = loaded_ruleset.rules[0]
        assert rule.name == "update_test"
        assert rule.action == RuleAction.DENY
        assert rule.priority == 75
        assert rule.description == "Updated description"
        assert rule.created_at is not None
        assert rule.updated_at is not None
        assert rule.updated_at != rule.created_at

    async def test_update_nonexistent_rule(self):
        rule = Rule(
            name="nonexistent_rule", scope=RuleScope.GLOBAL, action=RuleAction.ALLOW
        )

        with pytest.raises(RuleNotFoundError):
            await self.store.update_rule(rule)

    async def test_delete_rule(self):
        # Add a rule first
        rule = Rule(name="delete_test", scope=RuleScope.GLOBAL, action=RuleAction.ALLOW)

        await self.store.add_rule(rule)

        # Verify rule exists
        loaded_ruleset = await self.store.load_rules(RuleScope.GLOBAL)
        assert len(loaded_ruleset.rules) == 1

        # Delete the rule
        deleted = await self.store.delete_rule("delete_test", RuleScope.GLOBAL)
        assert deleted is True

        # Verify rule is gone
        loaded_ruleset = await self.store.load_rules(RuleScope.GLOBAL)
        assert len(loaded_ruleset.rules) == 0

    async def test_delete_nonexistent_rule(self):
        deleted = await self.store.delete_rule("nonexistent", RuleScope.GLOBAL)
        assert deleted is False

    async def test_get_rule(self):
        # Add a rule
        rule = Rule(
            name="get_test",
            scope=RuleScope.PROJECT,
            action=RuleAction.MODIFY,
            parameters={"test": "value"},
        )

        await self.store.add_rule(rule)

        # Get the rule by name and scope
        found_rule = await self.store.get_rule("get_test", RuleScope.PROJECT)
        assert found_rule is not None
        assert found_rule.name == "get_test"
        assert found_rule.scope == RuleScope.PROJECT
        assert found_rule.parameters == {"test": "value"}

        # Get rule by name only (should search all scopes)
        found_rule = await self.store.get_rule("get_test")
        assert found_rule is not None
        assert found_rule.name == "get_test"

    async def test_get_nonexistent_rule(self):
        found_rule = await self.store.get_rule("nonexistent")
        assert found_rule is None

    async def test_list_rules(self):
        # Add rules to different scopes
        global_rule = Rule(
            name="global_rule", scope=RuleScope.GLOBAL, action=RuleAction.ALLOW
        )
        project_rule = Rule(
            name="project_rule", scope=RuleScope.PROJECT, action=RuleAction.DENY
        )

        await self.store.add_rule(global_rule)
        await self.store.add_rule(project_rule)

        # List all rules
        all_rules = await self.store.list_rules()
        assert len(all_rules) == 2
        rule_names = [rule.name for rule in all_rules]
        assert "global_rule" in rule_names
        assert "project_rule" in rule_names

        # List rules by scope
        global_rules = await self.store.list_rules(RuleScope.GLOBAL)
        assert len(global_rules) == 1
        assert global_rules[0].name == "global_rule"

        project_rules = await self.store.list_rules(RuleScope.PROJECT)
        assert len(project_rules) == 1
        assert project_rules[0].name == "project_rule"

    async def test_backup_and_restore(self):
        # Create test data
        rule = Rule(
            name="backup_test",
            scope=RuleScope.GLOBAL,
            action=RuleAction.ALLOW,
            description="Test rule for backup",
        )

        await self.store.add_rule(rule)

        # Create backup
        backup_dir = Path(self.temp_dir) / "backup"
        await self.store.backup_rules(str(backup_dir))

        # Verify backup files exist
        assert (backup_dir / "global.yaml").exists()

        # Delete original data
        await self.store.delete_rule("backup_test", RuleScope.GLOBAL)
        rules = await self.store.list_rules()
        assert len(rules) == 0

        # Restore from backup
        await self.store.restore_rules(str(backup_dir))

        # Verify data is restored
        rules = await self.store.list_rules()
        assert len(rules) == 1
        assert rules[0].name == "backup_test"
        assert rules[0].description == "Test rule for backup"

    async def test_health_check(self):
        # Health check should pass for accessible directory
        healthy = await self.store.health_check()
        assert healthy is True

        # Health check should fail for non-accessible directory
        bad_store = YAMLRuleStore("/nonexistent/directory")
        healthy = await bad_store.health_check()
        assert healthy is False
