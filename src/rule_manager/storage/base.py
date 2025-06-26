from abc import ABC, abstractmethod

from ..models.base import Rule, RuleScope, RuleSet


class RuleStore(ABC):
    @abstractmethod
    async def load_rules(self, scope: RuleScope) -> RuleSet:
        pass

    @abstractmethod
    async def save_rules(self, ruleset: RuleSet) -> None:
        pass

    @abstractmethod
    async def get_rule(
        self, rule_name: str, scope: RuleScope | None = None
    ) -> Rule | None:
        pass

    @abstractmethod
    async def add_rule(self, rule: Rule) -> None:
        pass

    @abstractmethod
    async def update_rule(self, rule: Rule) -> None:
        pass

    @abstractmethod
    async def delete_rule(self, rule_name: str, scope: RuleScope) -> bool:
        pass

    @abstractmethod
    async def list_rules(self, scope: RuleScope | None = None) -> list[Rule]:
        pass

    @abstractmethod
    async def backup_rules(self, backup_path: str) -> None:
        pass

    @abstractmethod
    async def restore_rules(self, backup_path: str) -> None:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
