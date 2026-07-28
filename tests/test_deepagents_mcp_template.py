from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "deepagents" / "mcp"


@pytest.fixture
def rendered_mcp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    output = tmp_path / "rendered"
    output.mkdir()
    cookiecutter(str(TEMPLATE), output_dir=str(output), no_input=True)
    rendered = output / "mcp_deepagent"
    monkeypatch.syspath_prepend(str(rendered / "src"))
    return rendered


def load_rendered_module(rendered: Path, module_name: str) -> ModuleType:
    path = rendered / "src" / rendered.name / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"rendered_mcp_{module_name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(rendered: Path, payload: object) -> Path:
    path = rendered / "connections.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_mcp_config_normalizes_stdio_and_http(rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    monkeypatch.setenv("MCP_TOKEN", "secret-token")
    config_path = rendered_mcp / "connections.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "calculator": {
                        "transport": "stdio",
                        "command": "${PYTHON_EXECUTABLE}",
                        "args": ["-m", f"{rendered_mcp.name}.calculator_server"],
                    },
                    "orders": {
                        "transport": "http",
                        "url": "https://mcp.example.com/mcp",
                        "headers": {"Authorization": "Bearer ${MCP_TOKEN}"},
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = module.load_mcp_config(config_path)

    assert loaded.servers["calculator"]["command"] == sys.executable
    assert loaded.servers["orders"]["headers"]["Authorization"] == "Bearer secret-token"


def test_python_executable_placeholder_ignores_environment_override(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    monkeypatch.setenv("PYTHON_EXECUTABLE", "/tmp/untrusted-python")  # noqa: S108 - required hostile override
    loaded = module.load_mcp_config(rendered_mcp / ".mcp.json")
    assert loaded.servers["calculator"]["command"] == sys.executable


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        ({"mcpServers": {}}, "at least one server"),
        (
            {"mcpServers": {"bad name": {"transport": "stdio", "command": "python"}}},
            "server name",
        ),
        (
            {"mcpServers": {"x": {"transport": "sse", "url": "https://example.com"}}},
            "transport",
        ),
        (
            {
                "mcpServers": {
                    "x": {
                        "transport": "stdio",
                        "command": "python",
                        "url": "https://example.com",
                    }
                }
            },
            "unknown field",
        ),
        (
            {"mcpServers": {"x": {"transport": "http", "url": "relative"}}},
            "absolute http or https URL",
        ),
        (
            {"mcpServers": {"x": {"transport": "http", "url": "https://["}}},
            "absolute http or https URL",
        ),
    ],
)
def test_invalid_mcp_config_is_rejected(rendered_mcp: Path, payload: object, match: str) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = write_json(rendered_mcp, payload)
    with pytest.raises(module.MCPConfigError, match=match):
        module.load_mcp_config(path)


def test_duplicate_config_key_is_rejected(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = rendered_mcp / "connections.json"
    path.write_text(
        '{"mcpServers":{"x":{"transport":"stdio","command":"python","command":"python3"}}}',
        encoding="utf-8",
    )

    with pytest.raises(module.MCPConfigError, match="Duplicate key"):
        module.load_mcp_config(path)


def test_missing_secret_reference_is_rejected_without_leaking_ambient_value(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    ambient_value = "must-not-appear-in-errors"
    monkeypatch.setenv("MCP_SECRET", ambient_value)
    path = write_json(
        rendered_mcp,
        {
            "mcpServers": {
                "private": {
                    "transport": "http",
                    "url": "https://mcp.example.com/mcp",
                    "headers": {"Authorization": "Bearer ${MCP_SECRET}"},
                }
            }
        },
    )

    with pytest.raises(module.MCPConfigError, match="Missing environment variable") as exc:
        module.load_mcp_config(path, environ={})

    assert "MCP_SECRET" in str(exc.value)
    assert ambient_value not in str(exc.value)
