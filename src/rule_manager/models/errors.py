class RuleManagerError(Exception):
    def __init__(self, code: str, message: str, retry_allowed: bool = False):
        self.code = code
        self.message = message
        self.retry_allowed = retry_allowed
        super().__init__(f"{code}: {message}")


class RuleDSLSyntaxError(RuleManagerError):
    def __init__(self, message: str, expression: str = ""):
        super().__init__("E001", f"Rule DSL syntax error: {message}", retry_allowed=False)
        self.expression = expression


class PriorityConflictError(RuleManagerError):
    def __init__(self, message: str):
        super().__init__("E101", f"Priority conflict resolution failure: {message}", retry_allowed=True)


class StorageLockError(RuleManagerError):
    def __init__(self, message: str):
        super().__init__("E201", f"Storage lock failure: {message}", retry_allowed=True)


class UnexpectedError(RuleManagerError):
    def __init__(self, message: str):
        super().__init__("E500", f"Unexpected error: {message}", retry_allowed=True)


class CircularInheritanceError(RuleManagerError):
    def __init__(self, rule_chain: str):
        super().__init__("E002", f"Circular inheritance detected: {rule_chain}", retry_allowed=False)


class RuleNotFoundError(RuleManagerError):
    def __init__(self, rule_name: str):
        super().__init__("E003", f"Rule not found: {rule_name}", retry_allowed=False)


class InvalidRulesetVersionError(RuleManagerError):
    def __init__(self, version: str, min_version: str):
        super().__init__(
            "E004", 
            f"Ruleset version {version} is incompatible with minimum required version {min_version}", 
            retry_allowed=False
        )