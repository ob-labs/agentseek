"""Model-free smoke verification for the configured calculator MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import MCPConfig, load_mcp_config
from .mcp_tools import load_mcp_tools

_EXPECTED_TOOL_NAMES = ("calculator_add", "calculator_multiply")
_EXPECTED_ARGUMENTS = ("a", "b")
_EXPECTED_CALCULATION = "95"


class SmokeCheckError(RuntimeError):
    """Raised when the calculator MCP smoke contract is not satisfied."""


@dataclass(frozen=True)
class SmokeResult:
    tool_names: tuple[str, ...]
    required_arguments: tuple[str, ...]
    calculation: str


def _normalize_args_schema(args_schema: Any) -> dict[str, Any]:
    if isinstance(args_schema, dict):
        return args_schema
    model_json_schema = getattr(args_schema, "model_json_schema", None)
    if not callable(model_json_schema):
        raise SmokeCheckError("Calculator tool has an unsupported argument schema.")
    schema = model_json_schema()
    if not isinstance(schema, dict):
        raise SmokeCheckError("Calculator tool has an unsupported argument schema.")
    return schema


def _required_arguments(args_schema: Any) -> tuple[str, ...]:
    schema = _normalize_args_schema(args_schema)
    required = schema.get("required")
    if not isinstance(required, list) or not all(
        isinstance(argument, str) for argument in required
    ):
        raise SmokeCheckError("Calculator tool has invalid required arguments.")
    return tuple(required)


def _first_text_block(result: Any) -> str:
    if isinstance(result, list):
        for block in result:
            if (
                isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ):
                return block["text"]
    raise SmokeCheckError("Calculator tool returned no text result.")


async def run_smoke(config_path: Path) -> SmokeResult:
    """Discover and invoke the calculator without calling a language model."""
    config: MCPConfig = load_mcp_config(config_path)
    loaded = await load_mcp_tools(config)
    if loaded.tool_names != _EXPECTED_TOOL_NAMES:
        raise SmokeCheckError("Calculator MCP exposed unexpected tool names.")

    add_tool = next(tool for tool in loaded.tools if tool.name == "calculator_add")
    required_arguments = _required_arguments(add_tool.args_schema)
    if required_arguments != _EXPECTED_ARGUMENTS:
        raise SmokeCheckError("Calculator add tool has unexpected required arguments.")

    result = await add_tool.ainvoke({"a": 37, "b": 58})
    calculation = _first_text_block(result)
    if calculation != _EXPECTED_CALCULATION:
        raise SmokeCheckError("Calculator add tool returned an unexpected result.")

    return SmokeResult(
        tool_names=loaded.tool_names,
        required_arguments=required_arguments,
        calculation=calculation,
    )
