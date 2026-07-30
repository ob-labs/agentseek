"""Model-free smoke verification for stdio and Streamable HTTP MCP."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

from .config import MCPConfig, load_mcp_config
from .mcp_tools import load_mcp_tools

_EXPECTED_TOOL_NAMES = (
    "calculator_add",
    "calculator_multiply",
    "calculator_http_add",
    "calculator_http_multiply",
)
_EXPECTED_ARGUMENTS = ("a", "b")
_EXPECTED_STDIO_CALCULATION = "95"
_EXPECTED_HTTP_CALCULATION = "2146"
_HTTP_SERVER_NAME = "calculator_http"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_HTTP_SERVER_ENVIRONMENT_NAMES = frozenset(
    {
        "appdata",
        "homedrive",
        "homepath",
        "localappdata",
        "path",
        "pathext",
        "processor_architecture",
        "pythonhome",
        "pythonpath",
        "systemdrive",
        "systemroot",
        "temp",
        "tmp",
        "tmpdir",
        "username",
        "userprofile",
        "windir",
    }
)


class SmokeCheckError(RuntimeError):
    """Raised when the calculator MCP smoke contract is not satisfied."""


@dataclass(frozen=True)
class SmokeResult:
    tool_names: tuple[str, ...]
    required_arguments: tuple[str, ...]
    stdio_calculation: str
    http_calculation: str


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


def _calculator_http_address(config: MCPConfig) -> tuple[str, int]:
    connection = config.servers.get(_HTTP_SERVER_NAME)
    if connection is None or connection["transport"] != "http":
        raise SmokeCheckError("Smoke configuration must define calculator_http over HTTP.")
    parsed = urlparse(connection["url"])
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or parsed.path != "/mcp"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise SmokeCheckError("calculator_http must use a loopback http:// URL ending in /mcp.")
    return parsed.hostname, parsed.port or 80


def _http_server_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Keep only interpreter and platform values required by the child."""
    return {
        name: value
        for name, value in environ.items()
        if name.casefold() in _HTTP_SERVER_ENVIRONMENT_NAMES
    }


async def _http_server_is_ready(host: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=0.25)
    except (OSError, TimeoutError):
        return False

    host_header = f"[{host}]" if ":" in host else host
    try:
        writer.write(
            f"GET /health HTTP/1.1\r\nHost: {host_header}:{port}\r\nConnection: close\r\n\r\n".encode()
        )
        await asyncio.wait_for(writer.drain(), timeout=0.25)
        status_line = await asyncio.wait_for(reader.readline(), timeout=0.25)
        return status_line.startswith(b"HTTP/1.1 200")
    except (OSError, TimeoutError):
        return False
    finally:
        writer.close()
        await writer.wait_closed()


async def _wait_for_http_server(host: str, port: int, process: asyncio.subprocess.Process) -> None:
    for _attempt in range(100):
        if await _http_server_is_ready(host, port):
            return
        if process.returncode is not None:
            raise SmokeCheckError("Calculator HTTP MCP server exited before becoming ready.")
        await asyncio.sleep(0.1)
    raise SmokeCheckError("Calculator HTTP MCP server did not become ready.")


async def _stop_http_server(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except TimeoutError:
        process.kill()
        await process.wait()


@asynccontextmanager
async def _ensure_calculator_http_server(config: MCPConfig) -> AsyncIterator[None]:
    host, port = _calculator_http_address(config)
    if await _http_server_is_ready(host, port):
        yield
        return

    if not __package__:
        raise SmokeCheckError("Could not resolve the calculator HTTP server module.")
    process = await asyncio.create_subprocess_exec(  # noqa: S603 - current interpreter and bundled module
        sys.executable,
        "-m",
        f"{__package__}.calculator_http_server",
        "--host",
        host,
        "--port",
        str(port),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=_http_server_environment(os.environ),
    )
    try:
        await _wait_for_http_server(host, port, process)
        yield
    finally:
        await _stop_http_server(process)


async def run_smoke(config_path: Path) -> SmokeResult:
    """Discover and invoke calculators through both supported transports."""
    load_dotenv(dotenv_path=config_path.parent / ".env", override=False)
    config: MCPConfig = load_mcp_config(config_path)
    async with _ensure_calculator_http_server(config):
        loaded = await load_mcp_tools(config)
        if loaded.tool_names != _EXPECTED_TOOL_NAMES:
            raise SmokeCheckError("Calculator MCP exposed unexpected tool names.")

        stdio_tool = next(tool for tool in loaded.tools if tool.name == "calculator_add")
        http_tool = next(tool for tool in loaded.tools if tool.name == "calculator_http_multiply")
        required_arguments = _required_arguments(stdio_tool.args_schema)
        http_required_arguments = _required_arguments(http_tool.args_schema)
        if required_arguments != _EXPECTED_ARGUMENTS or http_required_arguments != _EXPECTED_ARGUMENTS:
            raise SmokeCheckError("Calculator tools have unexpected required arguments.")

        stdio_calculation = _first_text_block(await stdio_tool.ainvoke({"a": 37, "b": 58}))
        if stdio_calculation != _EXPECTED_STDIO_CALCULATION:
            raise SmokeCheckError("Calculator stdio tool returned an unexpected result.")

        http_calculation = _first_text_block(await http_tool.ainvoke({"a": 37, "b": 58}))
        if http_calculation != _EXPECTED_HTTP_CALCULATION:
            raise SmokeCheckError("Calculator HTTP tool returned an unexpected result.")

    return SmokeResult(
        tool_names=loaded.tool_names,
        required_arguments=required_arguments,
        stdio_calculation=stdio_calculation,
        http_calculation=http_calculation,
    )


def main() -> None:
    """Run the public model-free MCP smoke command."""
    result = asyncio.run(run_smoke(Path(".mcp.json")))
    print(
        "MCP smoke check passed: "
        f"tools={','.join(result.tool_names)}; "
        f"required_arguments={','.join(result.required_arguments)}; "
        f"stdio_calculation={result.stdio_calculation}; "
        f"http_calculation={result.http_calculation}"
    )


if __name__ == "__main__":
    main()
