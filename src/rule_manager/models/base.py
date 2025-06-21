from enum import Enum
from typing import Any, Dict, List, Optional
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
    conditions: Dict[str, Any] = Field(default_factory=dict)
    action: RuleAction
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parent_rule: Optional[str] = None
    inherits_from: Optional[List[str]] = None
    description: Optional[str] = None
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ruleset_version: str = "1.1"
    engine_min_version: str = ">=2.8.0"
    scope: RuleScope
    rules: List[Rule] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    model_name: Optional[str] = None
    prompt_length: Optional[int] = None
    timestamp: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_name: str
    action: RuleAction
    matched: bool
    parameters: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    priority: int
    execution_time_ms: Optional[float] = None


class RuleEvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: RuleContext
    results: List[RuleEvaluationResult]
    final_action: RuleAction
    total_execution_time_ms: float
    evaluated_at: str
    applicable_rules_count: int
    matched_rules_count: int