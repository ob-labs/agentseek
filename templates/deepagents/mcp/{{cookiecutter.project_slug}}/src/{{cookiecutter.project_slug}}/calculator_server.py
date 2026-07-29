"""Shared calculator tools and the stdio MCP entry point."""

from mcp.server.fastmcp import FastMCP


def create_calculator_server(*, host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    """Create an MCP server exposing deterministic calculator tools."""
    server = FastMCP("AgentSeek Calculator", host=host, port=port)

    @server.tool()
    def add(a: int, b: int) -> int:
        """Add two integers exactly."""
        return a + b

    @server.tool()
    def multiply(a: int, b: int) -> int:
        """Multiply two integers exactly."""
        return a * b

    return server


mcp = create_calculator_server()


if __name__ == "__main__":
    mcp.run(transport="stdio")
