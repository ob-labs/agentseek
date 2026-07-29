"""Streamable HTTP entry point for the local calculator MCP server."""

from __future__ import annotations

import argparse

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from .calculator_server import create_calculator_server


def create_http_server(*, host: str, port: int) -> FastMCP:
    """Create the calculator server with an HTTP readiness endpoint."""
    server = create_calculator_server(host=host, port=port)

    @server.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health_check(_request: Request) -> Response:
        return PlainTextResponse("ok")

    return server


def main() -> None:
    """Run the local calculator over Streamable HTTP."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default={{ cookiecutter.calculator_http_port }})
    args = parser.parse_args()
    create_http_server(host=args.host, port=args.port).run(transport="streamable-http")


if __name__ == "__main__":
    main()
