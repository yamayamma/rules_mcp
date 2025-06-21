import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .base import PriorityTieBreaking


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_RULE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    transport: Literal["stdio", "streamable-http", "sse"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    rules_dir: str = "config/rules"
    async_mode: bool = False
    
    # Storage settings
    storage_backend: Literal["yaml", "sqlite", "redis"] = "yaml"
    sqlite_path: str = "data/rules.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Rule engine settings
    priority_tie_breaking: PriorityTieBreaking = PriorityTieBreaking.FIFO
    enable_hot_reload: bool = True
    max_evaluation_time_ms: int = 1000
    
    # Security settings
    enable_auth: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Observability settings
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    enable_audit_log: bool = True
    audit_log_path: str = "logs/audit.db"
    
    # Performance settings
    max_concurrent_evaluations: int = 100
    cache_size_mb: int = 64
    
    def __init__(self, **data):
        # Backward compatibility with old prefix
        if "MCP_RULE_TRANSPORT" in os.environ:
            os.environ["FASTMCP_RULE_TRANSPORT"] = os.environ["MCP_RULE_TRANSPORT"]
        if "MCP_RULE_HOST" in os.environ:
            os.environ["FASTMCP_RULE_HOST"] = os.environ["MCP_RULE_HOST"]
        if "MCP_RULE_PORT" in os.environ:
            os.environ["FASTMCP_RULE_PORT"] = os.environ["MCP_RULE_PORT"]
        if "MCP_RULE_RULES_DIR" in os.environ:
            os.environ["FASTMCP_RULE_RULES_DIR"] = os.environ["MCP_RULE_RULES_DIR"]
        
        super().__init__(**data)


class CLISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RULE_CLI_",
        case_sensitive=False,
        extra="ignore",
    )
    
    config_file: Optional[str] = None
    env_file: Optional[str] = None
    verbose: bool = False
    debug: bool = False