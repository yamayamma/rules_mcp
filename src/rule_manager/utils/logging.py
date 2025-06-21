import logging
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_audit_log: bool = True,
    audit_log_path: str = "logs/audit.db"
) -> None:
    """
    Set up structured logging with structlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Log format (json, text)
        enable_audit_log: Whether to enable audit logging
        audit_log_path: Path to audit log database
    """
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure processors based on format
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """
    Audit logger for security-sensitive operations.
    Logs to both structured logs and append-only database.
    """
    
    def __init__(self, audit_log_path: Optional[str] = None):
        self.logger = get_logger("audit")
        self.audit_log_path = audit_log_path
    
    def log_rule_operation(
        self,
        operation: str,
        rule_name: str,
        scope: str,
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        **extra_context: Any
    ) -> None:
        """
        Log a rule operation for audit purposes.
        
        Args:
            operation: Type of operation (create, update, delete, evaluate)
            rule_name: Name of the rule
            scope: Scope of the rule
            user_id: ID of the user performing the operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
            **extra_context: Additional context to log
        """
        
        audit_data = {
            "event_type": "rule_operation",
            "operation": operation,
            "rule_name": rule_name,
            "scope": scope,
            "user_id": user_id,
            "success": success,
            "error_message": error_message,
            **extra_context
        }
        
        if success:
            self.logger.info("Rule operation completed", **audit_data)
        else:
            self.logger.error("Rule operation failed", **audit_data)
    
    def log_authentication(
        self,
        user_id: str,
        success: bool,
        method: str = "jwt",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an authentication attempt.
        
        Args:
            user_id: ID of the user attempting authentication
            success: Whether authentication was successful
            method: Authentication method used
            ip_address: IP address of the client
            user_agent: User agent string
            error_message: Error message if authentication failed
        """
        
        audit_data = {
            "event_type": "authentication",
            "user_id": user_id,
            "success": success,
            "method": method,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "error_message": error_message
        }
        
        if success:
            self.logger.info("Authentication successful", **audit_data)
        else:
            self.logger.warning("Authentication failed", **audit_data)
    
    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        required_permissions: Optional[list] = None,
        user_permissions: Optional[list] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an authorization check.
        
        Args:
            user_id: ID of the user
            resource: Resource being accessed
            action: Action being attempted
            success: Whether authorization was successful
            required_permissions: Permissions required for the action
            user_permissions: Permissions the user has
            error_message: Error message if authorization failed
        """
        
        audit_data = {
            "event_type": "authorization",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "required_permissions": required_permissions,
            "user_permissions": user_permissions,
            "error_message": error_message
        }
        
        if success:
            self.logger.info("Authorization granted", **audit_data)
        else:
            self.logger.warning("Authorization denied", **audit_data)
    
    def log_system_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        **extra_context: Any
    ) -> None:
        """
        Log a system event.
        
        Args:
            event_type: Type of system event
            message: Human-readable message
            severity: Severity level (debug, info, warning, error, critical)
            **extra_context: Additional context to log
        """
        
        audit_data = {
            "event_type": "system_event",
            "system_event_type": event_type,
            "message": message,
            **extra_context
        }
        
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method("System event", **audit_data)