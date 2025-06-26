from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    INDIVIDUAL = "individual"


class RuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    MODIFY = "modify"
    VALIDATE = "validate"


class PriorityTieBreaking(str, Enum):
    FIFO = "fifo"
    LEXICOGRAPHIC = "lexi"
    FIRST_WINS = "first"


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    scope: RuleScope
    priority: int = Field(ge=0, le=100, default=50)
    conditions: dict[str, Any] = Field(default_factory=dict)
    action: RuleAction
    parameters: dict[str, Any] = Field(default_factory=dict)
    parent_rule: str | None = None
    inherits_from: list[str] | None = None
    description: str | None = None
    enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class RuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ruleset_version: str = "1.1"
    engine_min_version: str = ">=2.8.0"
    scope: RuleScope
    rules: list[Rule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    model_name: str | None = None
    prompt_length: int | None = None
    timestamp: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_name: str
    action: RuleAction
    matched: bool
    parameters: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    priority: int
    execution_time_ms: float | None = None


class RuleEvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: RuleContext
    results: list[RuleEvaluationResult]
    final_action: RuleAction
    total_execution_time_ms: float
    evaluated_at: str
    applicable_rules_count: int
    matched_rules_count: int
