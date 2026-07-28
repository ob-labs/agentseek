"""Deterministic, all-or-nothing MCP tool discovery."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from .config import MCPConfig


class MCPDiscoveryError(RuntimeError):
    """Raised when any configured MCP server cannot expose its tools."""


@dataclass(frozen=True)
class LoadedMCPTools:
    client: MultiServerMCPClient
    tools: tuple[BaseTool, ...]
    tool_names: tuple[str, ...]


async def _load_server(
    client: MultiServerMCPClient, server_name: str
) -> list[BaseTool]:
    try:
        tools = await client.get_tools(server_name=server_name)
    except Exception:
        raise MCPDiscoveryError(
            f"MCP tool discovery failed for server {server_name!r}."
        ) from None
    if not tools:
        raise MCPDiscoveryError(f"MCP server {server_name!r} exposed no tools.")
    return tools


async def load_mcp_tools(config: MCPConfig) -> LoadedMCPTools:
    """Discover every configured server concurrently in stable server order."""
    client = MultiServerMCPClient(
        config.servers,
        tool_name_prefix=True,
        handle_tool_errors=True,
    )
    server_names = sorted(config.servers)
    tools_by_server = await asyncio.gather(
        *(_load_server(client, server_name) for server_name in server_names)
    )
    tools = tuple(tool for server_tools in tools_by_server for tool in server_tools)
    return LoadedMCPTools(
        client=client,
        tools=tools,
        tool_names=tuple(tool.name for tool in tools),
    )
