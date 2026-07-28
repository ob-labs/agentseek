"""Deterministic, all-or-nothing MCP tool discovery."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from .config import MCPConfig

# Exact ToolNode names observed with DeepAgents 0.6.12, the default
# StateBackend, and this template's disabled general-purpose subagent profile.
# `task` is intentionally absent; `execute` remains registered by the
# FilesystemMiddleware even though StateBackend cannot execute commands.
RESERVED_DEEPAGENTS_TOOL_NAMES = frozenset({
    "edit_file",
    "execute",
    "glob",
    "grep",
    "ls",
    "read_file",
    "write_file",
    "write_todos",
})


class MCPDiscoveryError(RuntimeError):
    """Raised when any configured MCP server cannot expose its tools."""


@dataclass(frozen=True)
class LoadedMCPTools:
    client: MultiServerMCPClient
    tools: tuple[BaseTool, ...]
    tool_names: tuple[str, ...]


async def _load_server(client: MultiServerMCPClient, server_name: str) -> list[BaseTool]:
    try:
        tools = await client.get_tools(server_name=server_name)
    except Exception:
        raise MCPDiscoveryError(f"MCP tool discovery failed for server {server_name!r}.") from None
    if not tools:
        raise MCPDiscoveryError(f"MCP server {server_name!r} exposed no tools.")
    return tools


def _source_tool_name(server_name: str, final_name: str) -> str:
    prefix = f"{server_name}_"
    return final_name.removeprefix(prefix)


def _validate_final_names(server_names: list[str], tools_by_server: list[list[BaseTool]]) -> None:
    origins: dict[str, tuple[str, str]] = {}
    for server_name, server_tools in zip(server_names, tools_by_server, strict=True):
        for tool in server_tools:
            final_name = tool.name
            source_name = _source_tool_name(server_name, final_name)
            if final_name in RESERVED_DEEPAGENTS_TOOL_NAMES:
                raise MCPDiscoveryError(
                    f"MCP tool {final_name!r} from server/tool pair "
                    f"{server_name!r}/{source_name!r} conflicts with an enabled "
                    "DeepAgents built-in tool."
                )
            if previous := origins.get(final_name):
                previous_server, previous_tool = previous
                raise MCPDiscoveryError(
                    f"MCP tool name {final_name!r} is duplicated by server/tool pairs "
                    f"{previous_server!r}/{previous_tool!r} and "
                    f"{server_name!r}/{source_name!r}."
                )
            origins[final_name] = (server_name, source_name)


async def load_mcp_tools(config: MCPConfig) -> LoadedMCPTools:
    """Discover every configured server concurrently in stable server order."""
    client = MultiServerMCPClient(
        config.servers,
        tool_name_prefix=True,
        handle_tool_errors=True,
    )
    server_names = sorted(config.servers)
    tasks = [asyncio.create_task(_load_server(client, server_name)) for server_name in server_names]
    try:
        tools_by_server = await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    _validate_final_names(server_names, tools_by_server)
    tools = tuple(tool for server_tools in tools_by_server for tool in server_tools)
    return LoadedMCPTools(
        client=client,
        tools=tools,
        tool_names=tuple(tool.name for tool in tools),
    )
