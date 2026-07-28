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


def test_connection_values_support_whole_and_embedded_environment_references(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = write_json(
        rendered_mcp,
        {
            "mcpServers": {
                "worker": {
                    "transport": "stdio",
                    "command": "${COMMAND}",
                    "args": ["${MODULE}", "--mode=${MODE}"],
                    "env": {"SERVICE_URL": "https://${SERVICE_HOST}/${SERVICE_PATH}"},
                },
                "remote": {
                    "transport": "http",
                    "url": "${MCP_URL}",
                    "headers": {"Authorization": "Bearer ${MCP_TOKEN}"},
                },
                "embedded": {
                    "transport": "http",
                    "url": "https://${MCP_HOST}:${MCP_PORT}/${MCP_PATH}",
                },
            }
        },
    )

    loaded = module.load_mcp_config(
        path,
        environ={
            "COMMAND": "python3",
            "MODULE": "-m",
            "MODE": "safe",
            "SERVICE_HOST": "service.example.com",
            "SERVICE_PATH": "v1",
            "MCP_URL": "https://mcp.example.com/mcp",
            "MCP_TOKEN": "token-value",
            "MCP_HOST": "embedded.example.com",
            "MCP_PORT": "8443",
            "MCP_PATH": "mcp",
        },
    )

    assert loaded.servers["worker"] == {
        "transport": "stdio",
        "command": "python3",
        "args": ["-m", "--mode=safe"],
        "env": {"SERVICE_URL": "https://service.example.com/v1"},
    }
    assert loaded.servers["remote"] == {
        "transport": "http",
        "url": "https://mcp.example.com/mcp",
        "headers": {"Authorization": "Bearer token-value"},
    }
    assert loaded.servers["embedded"]["url"] == "https://embedded.example.com:8443/mcp"


def test_empty_resolved_command_is_rejected(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = write_json(
        rendered_mcp,
        {"mcpServers": {"worker": {"transport": "stdio", "command": "${COMMAND}"}}},
    )

    with pytest.raises(module.MCPConfigError, match=r"non-empty string at \$\.mcpServers\.worker\.command") as exc:
        module.load_mcp_config(path, environ={"COMMAND": ""})

    assert exc.value.__cause__ is None
    assert exc.value.__context__ is None


def test_invalid_resolved_url_is_rejected_without_leaking_value_or_exception_chain(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    invalid_value = "[credential-like-host-value"
    path = write_json(
        rendered_mcp,
        {"mcpServers": {"remote": {"transport": "http", "url": "https://${HOST}/mcp"}}},
    )

    with pytest.raises(module.MCPConfigError, match=r"absolute http or https URL at \$\.mcpServers\.remote\.url") as exc:
        module.load_mcp_config(path, environ={"HOST": invalid_value})

    assert invalid_value not in str(exc.value)
    assert exc.value.__cause__ is None
    assert exc.value.__context__ is None


def test_server_name_with_dot_is_rejected(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = write_json(
        rendered_mcp,
        {"mcpServers": {"prod.billing": {"transport": "stdio", "command": "python"}}},
    )

    with pytest.raises(module.MCPConfigError, match="server name"):
        module.load_mcp_config(path)


@pytest.mark.parametrize(
    "url",
    [
        "http://:80/mcp",
        "http://user@/mcp",
        "https://bad host/mcp",
        "https://bad\thost/mcp",
        "https://example.com:/mcp",
        "https://example.com:bad/mcp",
        "https://example.com:0/mcp",
        "https://example.com:99999/mcp",
    ],
)
def test_malformed_http_authority_is_rejected(rendered_mcp: Path, url: str) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    path = write_json(
        rendered_mcp,
        {"mcpServers": {"remote": {"transport": "http", "url": url}}},
    )

    with pytest.raises(module.MCPConfigError, match=r"absolute http or https URL at \$\.mcpServers\.remote\.url"):
        module.load_mcp_config(path)


def test_invalid_resolved_host_is_rejected_without_leaking_value(rendered_mcp: Path) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    invalid_value = "sensitive host value"
    path = write_json(
        rendered_mcp,
        {"mcpServers": {"remote": {"transport": "http", "url": "https://${HOST}/mcp"}}},
    )

    with pytest.raises(module.MCPConfigError, match=r"absolute http or https URL at \$\.mcpServers\.remote\.url") as exc:
        module.load_mcp_config(path, environ={"HOST": invalid_value})

    assert invalid_value not in str(exc.value)
    assert exc.value.__cause__ is None
    assert exc.value.__context__ is None


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
