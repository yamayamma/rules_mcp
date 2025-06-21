# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM Hierarchical Rule Management MCP Server designed to manage global/project/individual level rules for LLM applications. The system provides centralized rule management with dynamic application and validation capabilities.

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastMCP 2.8.x+ with FastMCP Proxy
- **Configuration**: Pydantic v2 + pydantic-settings
- **Data Format**: YAML 1.2 for rule definitions and config files
- **Transport**: STDIO (default), Streamable HTTP, SSE
- **Storage**: YAML files, SQLite, or Redis with appropriate locking mechanisms

## Project Structure

When implementing this project, follow this recommended structure:

```
src/
├── rule_manager/
│   ├── core/           # Rule engine and DSL
│   ├── storage/        # Storage abstractions (YAML, SQLite, Redis)
│   ├── transport/      # Transport layer (STDIO, HTTP, SSE)
│   ├── security/       # Authentication, authorization, audit logging
│   └── models/         # Pydantic models
config/
├── rules/              # YAML rule definitions
└── settings/           # Configuration files
tests/
├── unit/              # Unit tests with pytest
├── integration/       # Integration tests
└── load/              # Load testing with locust
```

## Development Commands

Since this project is in design phase, here are the expected commands based on the specification:

### Project Setup
```bash
# Initialize Python project with Poetry
poetry init
poetry install

# Setup development environment
poetry install --with dev
pre-commit install
```

### Testing
```bash
# Run unit tests
poetry run pytest tests/unit/

# Run integration tests  
poetry run pytest tests/integration/

# Run load tests
poetry run locust -f tests/load/

# Security scanning
poetry run bandit -r src/
```

### Code Quality
```bash
# Format code
poetry run black src/ tests/
poetry run ruff check src/ tests/

# Type checking
poetry run mypy src/
```

### Server Operations
```bash
# Run server (STDIO mode - default)
poetry run rule-manager

# Run server with HTTP transport
poetry run rule-manager --transport streamable-http

# Run with custom config
poetry run rule-manager --env-file .env.prod
```

## Key Architecture Concepts

### Rule Engine
- Rules have hierarchical scope (global/project/individual)
- Priority-based evaluation with configurable tie-breaking
- Safe DSL evaluation using filtrex (not eval/exec)
- Circular inheritance detection at startup
- Hot reload capability with file watching

### Transport Strategy
- Primary: STDIO for local CLI/IDE integration
- Secondary: Streamable HTTP for remote/web usage
- Legacy: SSE support for older clients
- One process per transport with FastMCP Proxy for bridging

### Storage & Concurrency
- Abstract RuleStore interface for multiple backends
- File locking with portalocker for YAML
- WAL transactions for SQLite
- Lua transactions for Redis
- Audit logging with append-only SQLite + checksums

### Security Model
- Bearer JWT authentication with scope-based permissions
- Three permission levels: rules:read, rules:write, rules:admin
- Rate limiting via nginx/Caddy or fallback slowapi
- Structured audit logging with who/when/what

## Configuration Management

Settings use Pydantic with environment variable overrides:
- Prefix: `FASTMCP_RULE_*`
- Config file: `.env` (UTF-8)
- Backward compatibility with `MCP_RULE_*` prefix

## Error Handling

Standard error codes are defined:
- E001 (400): Rule DSL syntax error
- E101 (409): Priority conflict resolution failure  
- E201 (423): YAML exclusive lock failure
- E500 (500): Unexpected exception

## Performance Targets

- Rule evaluation response: < 100ms (p95) for 100 concurrent sessions
- Memory consumption: < 256MB for 1k rules with cache
- Disk IOPS: < 500 for SQLite WAL mode

## Testing Strategy

- Unit tests: 90% coverage target with InMemoryClient
- Load tests: 100 concurrent sessions < 100ms response time
- Migration tests: YAML→SQLite and SSE→HTTP transitions
- Security tests: Zero high-severity findings with bandit/trivy