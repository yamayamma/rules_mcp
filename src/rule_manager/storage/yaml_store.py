import os
import asyncio
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import portalocker

from .base import RuleStore
from ..models.base import Rule, RuleSet, RuleScope
from ..models.errors import StorageLockError, RuleNotFoundError, UnexpectedError


class YAMLRuleStore(RuleStore):
    def __init__(self, rules_dir: str):
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self._file_locks: Dict[str, asyncio.Lock] = {}

    def _get_file_path(self, scope: RuleScope) -> Path:
        return self.rules_dir / f"{scope.value}.yaml"

    def _get_lock(self, file_path: str) -> asyncio.Lock:
        if file_path not in self._file_locks:
            self._file_locks[file_path] = asyncio.Lock()
        return self._file_locks[file_path]

    async def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}

        try:
            async with self._get_lock(str(file_path)):
                with open(file_path, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    try:
                        content = yaml.safe_load(f) or {}
                        return content
                    finally:
                        portalocker.unlock(f)
        except Exception as e:
            if "lock" in str(e).lower():
                raise StorageLockError(f"Failed to acquire read lock for {file_path}")
            raise UnexpectedError(f"Failed to load YAML file {file_path}: {e}")

    async def _save_yaml_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        try:
            async with self._get_lock(str(file_path)):
                with open(file_path, "w", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_EX)
                    try:
                        yaml.safe_dump(
                            data,
                            f,
                            default_flow_style=False,
                            allow_unicode=True,
                            sort_keys=False,
                        )
                    finally:
                        portalocker.unlock(f)
        except Exception as e:
            if "lock" in str(e).lower():
                raise StorageLockError(f"Failed to acquire write lock for {file_path}")
            raise UnexpectedError(f"Failed to save YAML file {file_path}: {e}")

    async def load_rules(self, scope: RuleScope) -> RuleSet:
        file_path = self._get_file_path(scope)
        data = await self._load_yaml_file(file_path)

        if not data:
            return RuleSet(scope=scope, rules=[])

        try:
            return RuleSet(**data)
        except Exception as e:
            raise UnexpectedError(f"Failed to parse ruleset from {file_path}: {e}")

    async def save_rules(self, ruleset: RuleSet) -> None:
        file_path = self._get_file_path(ruleset.scope)

        # Update timestamps
        now = datetime.utcnow().isoformat()
        for rule in ruleset.rules:
            if not rule.created_at:
                rule.created_at = now
            rule.updated_at = now

        ruleset_dict = ruleset.model_dump(mode='json')
        await self._save_yaml_file(file_path, ruleset_dict)

    async def get_rule(
        self, rule_name: str, scope: Optional[RuleScope] = None
    ) -> Optional[Rule]:
        if scope:
            scopes = [scope]
        else:
            scopes = list(RuleScope)

        for scope_to_check in scopes:
            ruleset = await self.load_rules(scope_to_check)
            for rule in ruleset.rules:
                if rule.name == rule_name:
                    return rule

        return None

    async def add_rule(self, rule: Rule) -> None:
        ruleset = await self.load_rules(rule.scope)

        # Check if rule already exists
        existing_rule = next((r for r in ruleset.rules if r.name == rule.name), None)
        if existing_rule:
            raise UnexpectedError(
                f"Rule {rule.name} already exists in scope {rule.scope}"
            )

        rule.created_at = datetime.utcnow().isoformat()
        rule.updated_at = rule.created_at
        ruleset.rules.append(rule)
        await self.save_rules(ruleset)

    async def update_rule(self, rule: Rule) -> None:
        ruleset = await self.load_rules(rule.scope)

        for i, existing_rule in enumerate(ruleset.rules):
            if existing_rule.name == rule.name:
                rule.created_at = existing_rule.created_at
                rule.updated_at = datetime.utcnow().isoformat()
                ruleset.rules[i] = rule
                await self.save_rules(ruleset)
                return

        raise RuleNotFoundError(rule.name)

    async def delete_rule(self, rule_name: str, scope: RuleScope) -> bool:
        ruleset = await self.load_rules(scope)

        for i, rule in enumerate(ruleset.rules):
            if rule.name == rule_name:
                ruleset.rules.pop(i)
                await self.save_rules(ruleset)
                return True

        return False

    async def list_rules(self, scope: Optional[RuleScope] = None) -> List[Rule]:
        if scope:
            scopes = [scope]
        else:
            scopes = list(RuleScope)

        all_rules = []
        for scope_to_check in scopes:
            ruleset = await self.load_rules(scope_to_check)
            all_rules.extend(ruleset.rules)

        return all_rules

    async def backup_rules(self, backup_path: str) -> None:
        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        for scope in RuleScope:
            source_path = self._get_file_path(scope)
            if source_path.exists():
                dest_path = backup_dir / f"{scope.value}.yaml"
                data = await self._load_yaml_file(source_path)
                await self._save_yaml_file(dest_path, data)

    async def restore_rules(self, backup_path: str) -> None:
        backup_dir = Path(backup_path)

        for scope in RuleScope:
            backup_file = backup_dir / f"{scope.value}.yaml"
            if backup_file.exists():
                dest_path = self._get_file_path(scope)
                data = await self._load_yaml_file(backup_file)
                await self._save_yaml_file(dest_path, data)

    async def health_check(self) -> bool:
        try:
            # Check if directory is accessible
            if not self.rules_dir.exists():
                return False

            # Test write access by creating a temporary file
            test_file = self.rules_dir / ".health_check"
            test_file.write_text("health_check")
            test_file.unlink()

            return True
        except Exception:
            return False
