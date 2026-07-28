"""A model-free calculator MCP server for local verification."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AgentSeek Calculator")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers exactly."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two integers exactly."""
    return a * b


if __name__ == "__main__":
    mcp.run(transport="stdio")
