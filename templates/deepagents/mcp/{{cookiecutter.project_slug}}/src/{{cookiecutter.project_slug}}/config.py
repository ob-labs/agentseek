"""Strict loading and normalization for MCP server connections."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast
from urllib.parse import urlparse

_ENVIRONMENT_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_SERVER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
_INVALID_URL_CHARACTER = re.compile(r"[\s\x00-\x1f\x7f-\x9f]")


class MCPConfigError(ValueError):
    """Raised when .mcp.json cannot be normalized safely."""


class StdioConnection(TypedDict):
    transport: Literal["stdio"]
    command: str
    args: list[str]
    env: NotRequired[dict[str, str]]


class HttpConnection(TypedDict):
    transport: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]


@dataclass(frozen=True)
class MCPConfig:
    servers: dict[str, StdioConnection | HttpConnection]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise MCPConfigError("Duplicate key in MCP configuration")
        parsed[key] = value
    return parsed


def _require_string(value: Any, json_path: str) -> None:
    if not isinstance(value, str):
        raise MCPConfigError(f"Expected a string at {json_path}")


def _require_non_empty_string(value: str, json_path: str) -> None:
    if not value:
        raise MCPConfigError(f"Expected a non-empty string at {json_path}")


def _validate_string_mapping(value: Any, json_path: str) -> None:
    if not isinstance(value, dict):
        raise MCPConfigError(f"Expected an object at {json_path}")
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise MCPConfigError(f"Expected string keys and values at {json_path}")


def _validate_stdio(connection: dict[str, Any], json_path: str) -> None:
    if not set(connection) <= {"transport", "command", "args", "env"}:
        raise MCPConfigError(f"Found unknown field at {json_path}")
    if "command" not in connection:
        raise MCPConfigError(f"Missing required field at {json_path}.command")
    _require_string(connection["command"], f"{json_path}.command")
    if "args" in connection:
        args = connection["args"]
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise MCPConfigError(f"Expected a list of strings at {json_path}.args")
    if "env" in connection:
        _validate_string_mapping(connection["env"], f"{json_path}.env")


def _validate_http(connection: dict[str, Any], json_path: str) -> None:
    if not set(connection) <= {"transport", "url", "headers"}:
        raise MCPConfigError(f"Found unknown field at {json_path}")
    if "url" not in connection:
        raise MCPConfigError(f"Missing required field at {json_path}.url")
    url = connection["url"]
    _require_string(url, f"{json_path}.url")
    if "headers" in connection:
        _validate_string_mapping(connection["headers"], f"{json_path}.headers")


def _is_absolute_http_url(url: str) -> bool:
    if _INVALID_URL_CHARACTER.search(url) is not None:
        return False
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port
    except ValueError:
        return False
    if parsed_url.scheme not in {"http", "https"} or not hostname or parsed_url.netloc.endswith(":"):
        return False
    return port is None or 1 <= port <= 65535


def _validate_config(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MCPConfigError("MCP configuration must be an object")
    if set(value) != {"mcpServers"}:
        raise MCPConfigError("MCP configuration must contain only mcpServers")
    servers = value["mcpServers"]
    if not isinstance(servers, dict):
        raise MCPConfigError("mcpServers must be an object")
    if not servers:
        raise MCPConfigError("mcpServers must define at least one server")

    for server_name, connection in servers.items():
        if not isinstance(server_name, str) or _SERVER_NAME.fullmatch(server_name) is None:
            raise MCPConfigError("Invalid MCP server name")
        json_path = f"$.mcpServers.{server_name}"
        if not isinstance(connection, dict):
            raise MCPConfigError(f"Expected an object at {json_path}")
        transport = connection.get("transport")
        if transport == "stdio":
            _validate_stdio(connection, json_path)
        elif transport == "http":
            _validate_http(connection, json_path)
        else:
            raise MCPConfigError(f"Unsupported transport at {json_path}.transport")
    return value


def _validate_resolved_connections(value: dict[str, Any]) -> None:
    for server_name, connection in value["mcpServers"].items():
        json_path = f"$.mcpServers.{server_name}"
        if connection["transport"] == "stdio":
            _require_non_empty_string(connection["command"], f"{json_path}.command")
            continue

        url = connection["url"]
        _require_non_empty_string(url, f"{json_path}.url")
        if not _is_absolute_http_url(url):
            raise MCPConfigError(f"Expected an absolute http or https URL at {json_path}.url")


def _normalize_connections(value: dict[str, Any]) -> None:
    for connection in value["mcpServers"].values():
        if connection["transport"] == "stdio":
            connection.setdefault("args", [])


def _resolve(value: Any, environment: Mapping[str, str], json_path: str) -> Any:
    if isinstance(value, str):

        def replacement(match: re.Match[str]) -> str:
            name = match.group(1)
            if name == "PYTHON_EXECUTABLE":
                return sys.executable
            resolved = environment.get(name)
            if resolved is None:
                raise MCPConfigError(f"Missing environment variable referenced by {json_path}: {name}")
            return resolved

        return _ENVIRONMENT_REFERENCE.sub(replacement, value)
    if isinstance(value, list):
        return [_resolve(item, environment, f"{json_path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, dict):
        return {key: _resolve(item, environment, f"{json_path}.{key}") for key, item in value.items()}
    return value


def load_mcp_config(path: Path, environ: Mapping[str, str] | None = None) -> MCPConfig:
    """Load, strictly validate, and interpolate an MCP JSON configuration."""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise MCPConfigError(f"Could not read MCP configuration: {path}") from exc

    try:
        unresolved = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except MCPConfigError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise MCPConfigError("MCP configuration is not valid JSON") from exc

    validated = _validate_config(unresolved)
    environment = os.environ if environ is None else environ
    resolved = _resolve(validated, environment, "$")
    _normalize_connections(resolved)
    _validate_resolved_connections(resolved)
    return MCPConfig(servers=cast(dict[str, StdioConnection | HttpConnection], resolved["mcpServers"]))
