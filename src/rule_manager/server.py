import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel

from .models.base import (
    Rule,
    RuleSet,
    RuleScope,
    RuleAction,
    RuleContext,
    RuleEvaluationSummary,
    PriorityTieBreaking,
)
from .models.settings import ServerSettings
from .models.errors import RuleManagerError
from .core.engine import RuleEngine
from .storage.yaml_store import YAMLRuleStore


class CreateRuleRequest(BaseModel):
    name: str
    scope: RuleScope
    priority: int = 50
    conditions: Dict[str, Any] = {}
    action: RuleAction
    parameters: Dict[str, Any] = {}
    parent_rule: Optional[str] = None
    inherits_from: Optional[List[str]] = None
    description: Optional[str] = None
    enabled: bool = True


class UpdateRuleRequest(BaseModel):
    name: str
    scope: RuleScope
    priority: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    action: Optional[RuleAction] = None
    parameters: Optional[Dict[str, Any]] = None
    parent_rule: Optional[str] = None
    inherits_from: Optional[List[str]] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class EvaluateRulesRequest(BaseModel):
    context: RuleContext


class RuleManagerServer:
    def __init__(self, settings: ServerSettings):
        self.settings = settings
        self.mcp = FastMCP("Rule Manager")

        # Initialize storage
        if settings.storage_backend == "yaml":
            self.rule_store = YAMLRuleStore(settings.rules_dir)
        else:
            raise NotImplementedError(
                f"Storage backend {settings.storage_backend} not implemented"
            )

        # Initialize rule engine
        self.rule_engine = RuleEngine(
            rule_store=self.rule_store,
            priority_tie_breaking=settings.priority_tie_breaking,
            max_evaluation_time_ms=settings.max_evaluation_time_ms,
        )

        # Register MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def evaluate_rules(request: EvaluateRulesRequest) -> Dict[str, Any]:
            """
            Evaluate rules against a given context and return the results.

            Args:
                request: The evaluation request containing the context

            Returns:
                Dictionary containing evaluation results
            """
            try:
                result = await self.rule_engine.evaluate_rules(request.context)
                return result.model_dump()
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def create_rule(request: CreateRuleRequest) -> Dict[str, Any]:
            """
            Create a new rule.

            Args:
                request: The rule creation request

            Returns:
                Dictionary containing the created rule or error information
            """
            try:
                rule = Rule(
                    name=request.name,
                    scope=request.scope,
                    priority=request.priority,
                    conditions=request.conditions,
                    action=request.action,
                    parameters=request.parameters,
                    parent_rule=request.parent_rule,
                    inherits_from=request.inherits_from,
                    description=request.description,
                    enabled=request.enabled,
                    created_at=datetime.utcnow().isoformat(),
                )

                await self.rule_store.add_rule(rule)
                return {"success": True, "rule": rule.model_dump()}
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def update_rule(request: UpdateRuleRequest) -> Dict[str, Any]:
            """
            Update an existing rule.

            Args:
                request: The rule update request

            Returns:
                Dictionary containing the updated rule or error information
            """
            try:
                # Get existing rule
                existing_rule = await self.rule_store.get_rule(
                    request.name, request.scope
                )
                if not existing_rule:
                    return {
                        "error": {
                            "code": "E003",
                            "message": f"Rule not found: {request.name}",
                            "retry_allowed": False,
                        }
                    }

                # Update fields
                updated_data = existing_rule.model_dump()
                for field, value in request.model_dump(exclude_unset=True).items():
                    if (
                        field != "name" and field != "scope"
                    ):  # Don't allow changing name/scope
                        updated_data[field] = value

                updated_data["updated_at"] = datetime.utcnow().isoformat()
                updated_rule = Rule(**updated_data)

                await self.rule_store.update_rule(updated_rule)
                return {"success": True, "rule": updated_rule.model_dump()}
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def delete_rule(rule_name: str, scope: str) -> Dict[str, Any]:
            """
            Delete a rule.

            Args:
                rule_name: Name of the rule to delete
                scope: Scope of the rule (global, project, individual)

            Returns:
                Dictionary containing success status or error information
            """
            try:
                rule_scope = RuleScope(scope)
                deleted = await self.rule_store.delete_rule(rule_name, rule_scope)

                if deleted:
                    return {"success": True, "message": f"Rule '{rule_name}' deleted"}
                else:
                    return {
                        "error": {
                            "code": "E003",
                            "message": f"Rule not found: {rule_name}",
                            "retry_allowed": False,
                        }
                    }
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def list_rules(scope: Optional[str] = None) -> Dict[str, Any]:
            """
            List all rules, optionally filtered by scope.

            Args:
                scope: Optional scope filter (global, project, individual)

            Returns:
                Dictionary containing list of rules or error information
            """
            try:
                rule_scope = RuleScope(scope) if scope else None
                rules = await self.rule_store.list_rules(rule_scope)

                return {
                    "success": True,
                    "rules": [rule.model_dump() for rule in rules],
                    "count": len(rules),
                }
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def get_rule(
            rule_name: str, scope: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Get a specific rule by name and optional scope.

            Args:
                rule_name: Name of the rule to retrieve
                scope: Optional scope filter (global, project, individual)

            Returns:
                Dictionary containing the rule or error information
            """
            try:
                rule_scope = RuleScope(scope) if scope else None
                rule = await self.rule_store.get_rule(rule_name, rule_scope)

                if rule:
                    return {"success": True, "rule": rule.model_dump()}
                else:
                    return {
                        "error": {
                            "code": "E003",
                            "message": f"Rule not found: {rule_name}",
                            "retry_allowed": False,
                        }
                    }
            except RuleManagerError as e:
                return {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "retry_allowed": e.retry_allowed,
                    }
                }
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def validate_rule_dsl(expression: str) -> Dict[str, Any]:
            """
            Validate a rule DSL expression.

            Args:
                expression: The DSL expression to validate

            Returns:
                Dictionary containing validation results
            """
            try:
                issues = self.rule_engine.dsl_evaluator.validate_expression(expression)

                return {"success": True, "valid": len(issues) == 0, "issues": issues}
            except Exception as e:
                return {
                    "error": {
                        "code": "E500",
                        "message": f"Unexpected error: {str(e)}",
                        "retry_allowed": True,
                    }
                }

        @self.mcp.tool()
        async def health_check() -> Dict[str, Any]:
            """
            Perform a health check of the rule manager service.

            Returns:
                Dictionary containing health status
            """
            try:
                storage_healthy = await self.rule_store.health_check()

                return {
                    "success": True,
                    "healthy": storage_healthy,
                    "storage_backend": self.settings.storage_backend,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                return {
                    "success": False,
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
