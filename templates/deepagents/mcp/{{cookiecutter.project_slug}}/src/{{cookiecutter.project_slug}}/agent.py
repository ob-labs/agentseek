"""Lazy DeepAgents graph assembly from configured MCP tools."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from langgraph.graph.state import CompiledStateGraph

from .config import load_mcp_config
from .mcp_tools import load_mcp_tools
from .model import build_model, model_profile_key


@dataclass(frozen=True)
class RuntimeBundle:
    """Resources retained for the lifetime of a successfully built graph."""

    client: object
    tool_names: tuple[str, ...]
    graph: CompiledStateGraph


_runtime: RuntimeBundle | None = None
_runtime_lock = asyncio.Lock()


async def _build_runtime() -> RuntimeBundle:
    config = load_mcp_config(Path(".mcp.json"))
    model = build_model()
    loaded = await load_mcp_tools(config)
    profile = HarnessProfile(
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    )
    register_harness_profile(model_profile_key(), profile)
    graph = create_deep_agent(
        model=model,
        tools=list(loaded.tools),
        subagents=[],
        system_prompt=(
            "You are an assistant connected to external tools through MCP. "
            "Use the available tools when they are relevant. "
            "Answer in the same language as the user's question."
        ),
    )
    return RuntimeBundle(
        client=loaded.client,
        tool_names=loaded.tool_names,
        graph=graph,
    )


async def make_graph() -> CompiledStateGraph:
    """Return the cached graph, building one complete runtime on first use."""
    global _runtime
    if _runtime is not None:
        return _runtime.graph
    async with _runtime_lock:
        if _runtime is None:
            _runtime = await _build_runtime()
        return _runtime.graph
