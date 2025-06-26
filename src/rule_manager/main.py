#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from .models.settings import ServerSettings
from .server import RuleManagerServer


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLM Hierarchical Rule Management MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default STDIO transport
  rule-manager

  # Run with HTTP transport
  rule-manager --transport streamable-http --port 8080

  # Run with custom rules directory
  rule-manager --rules-dir /path/to/rules

  # Run with environment file
  rule-manager --env-file .env.production
        """,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        help="Transport protocol to use (default: stdio)",
    )

    parser.add_argument(
        "--host", help="Host to bind to for HTTP/SSE transports (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to for HTTP/SSE transports (default: 8000)",
    )

    parser.add_argument(
        "--rules-dir", help="Directory containing rule files (default: config/rules)"
    )

    parser.add_argument(
        "--storage-backend",
        choices=["yaml", "sqlite", "redis"],
        help="Storage backend to use (default: yaml)",
    )

    parser.add_argument(
        "--priority-tie",
        choices=["fifo", "lexi", "first"],
        help="Priority tie-breaking strategy (default: fifo)",
    )

    parser.add_argument("--env-file", help="Environment file to load (default: .env)")

    parser.add_argument("--config-file", help="Configuration file to load")

    parser.add_argument(
        "--async-mode",
        action="store_true",
        help="Enable async mode for high concurrency",
    )

    parser.add_argument(
        "--disable-auth",
        action="store_true",
        help="Disable authentication (not recommended for production)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument("--version", action="version", version="rule-manager 0.1.0")

    return parser


def load_settings_from_args(args: argparse.Namespace) -> ServerSettings:
    """Load settings from command line arguments and environment"""

    # Build settings kwargs from args
    settings_kwargs = {}

    if args.transport:
        settings_kwargs["transport"] = args.transport
    if args.host:
        settings_kwargs["host"] = args.host
    if args.port:
        settings_kwargs["port"] = args.port
    if args.rules_dir:
        settings_kwargs["rules_dir"] = args.rules_dir
    if args.storage_backend:
        settings_kwargs["storage_backend"] = args.storage_backend
    if args.priority_tie:
        priority_map = {"fifo": "fifo", "lexi": "lexi", "first": "first"}
        settings_kwargs["priority_tie_breaking"] = priority_map[args.priority_tie]
    if args.async_mode:
        settings_kwargs["async_mode"] = True
    if args.disable_auth:
        settings_kwargs["enable_auth"] = False
    if args.log_level:
        settings_kwargs["log_level"] = args.log_level
    if args.verbose:
        settings_kwargs["log_level"] = "DEBUG"

    # Handle environment file
    if args.env_file:
        # Override the default env_file in model_config

        if Path(args.env_file).exists():
            settings_kwargs["_env_file"] = args.env_file
        else:
            print(f"Warning: Environment file {args.env_file} not found")

    return ServerSettings(**settings_kwargs)



def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load settings
        settings = load_settings_from_args(args)

        # Create server
        server = RuleManagerServer(settings)

        print("Starting Rule Manager MCP Server...")
        print(f"Transport: {settings.transport}")
        if settings.transport != "stdio":
            print(f"Address: {settings.host}:{settings.port}")
        print(f"Rules Directory: {settings.rules_dir}")
        print(f"Storage Backend: {settings.storage_backend}")

        # Let FastMCP handle the event loop
        if settings.transport == "stdio":
            server.mcp.run(transport="stdio")
        elif settings.transport == "streamable-http":
            server.mcp.run(
                transport="streamable-http",
                host=settings.host,
                port=settings.port,
                async_mode=settings.async_mode
            )
        elif settings.transport == "sse":
            server.mcp.run(
                transport="sse",
                host=settings.host,
                port=settings.port
            )
        else:
            raise ValueError(f"Unsupported transport: {settings.transport}")

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
