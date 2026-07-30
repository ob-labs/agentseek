from __future__ import annotations

import ast
import asyncio
import importlib
import importlib.util
import inspect
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Protocol, cast

import pytest
from cookiecutter.main import cookiecutter
from pydantic import SecretStr

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "deepagents" / "mcp"
CHARACTERIZED_DEEPAGENTS_VERSION = "0.6.12"


class _GeneralPurposeSubagentProfileLike(Protocol):
    enabled: bool | None


class _HarnessProfileLike(Protocol):
    general_purpose_subagent: _GeneralPurposeSubagentProfileLike


class _NamedTool(Protocol):
    name: str


class _NamedModel(Protocol):
    model_name: str


class _LoadedToolsLike(Protocol):
    tool_names: tuple[str, ...]


class _DescribedToolLike(Protocol):
    description: str


class _ToolRegistryLike(Protocol):
    tools_by_name: dict[str, object]


class _ToolNodeLike(Protocol):
    bound: _ToolRegistryLike


@pytest.fixture
def rendered_mcp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    output = tmp_path / "rendered"
    output.mkdir()
    cookiecutter(str(TEMPLATE), output_dir=str(output), no_input=True)
    rendered = output / "mcp_deepagent"
    monkeypatch.syspath_prepend(str(rendered / "src"))
    return rendered


@pytest.fixture
def rendered_agent(rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Import the generated boundary against the public DeepAgents 0.6.12 surface.

    The repository test environment is still on DeepAgents 0.6.10, so provide
    only the two profile classes and registry function introduced in 0.6.12.
    Individual tests replace hosted/model and graph construction boundaries.
    """
    import deepagents

    @dataclass(frozen=True)
    class GeneralPurposeSubagentProfile:
        enabled: bool | None = None

    @dataclass(frozen=True)
    class HarnessProfile:
        general_purpose_subagent: GeneralPurposeSubagentProfile | None = None

    monkeypatch.setattr(
        deepagents,
        "GeneralPurposeSubagentProfile",
        GeneralPurposeSubagentProfile,
        raising=False,
    )
    monkeypatch.setattr(deepagents, "HarnessProfile", HarnessProfile, raising=False)
    monkeypatch.setattr(deepagents, "register_harness_profile", lambda _key, _profile: None, raising=False)
    return import_rendered_package_module(rendered_mcp, "agent")


def load_rendered_module(rendered: Path, module_name: str) -> ModuleType:
    path = rendered / "src" / rendered.name / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"rendered_mcp_{module_name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def import_rendered_package_module(rendered: Path, module_name: str) -> ModuleType:
    for imported_name in tuple(sys.modules):
        if imported_name == rendered.name or imported_name.startswith(f"{rendered.name}."):
            del sys.modules[imported_name]
    importlib.invalidate_caches()
    return importlib.import_module(f"{rendered.name}.{module_name}")


def write_json(rendered: Path, payload: object) -> Path:
    path = rendered / "connections.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _unused_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _configure_calculator_http_port(rendered: Path) -> int:
    port = _unused_loopback_port()
    config_path = rendered / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["mcpServers"]["calculator_http"]["url"] = f"http://127.0.0.1:{port}/mcp"
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    return port


def _loopback_port_is_open(port: int) -> bool:
    with socket.socket() as client:
        client.settimeout(0.1)
        return client.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_loopback_port(port: int) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if _loopback_port_is_open(port):
            return
        time.sleep(0.05)
    pytest.fail(f"HTTP server did not listen on port {port}")


def prepare_rendered_mcp_subprocess(rendered: Path, *, server_name: str = "calculator") -> tuple[dict[str, str], int]:
    source_root = rendered / "src"
    http_port = _configure_calculator_http_port(rendered)
    config_path = rendered / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    calculator = config_payload["mcpServers"].pop("calculator")
    calculator["env"] = {"PYTHONPATH": "${PYTHONPATH}"}
    config_payload["mcpServers"][server_name] = calculator
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    return {**os.environ, "PYTHONPATH": str(source_root)}, http_port


def _write_python_command(directory: Path, name: str, source: str) -> Path:
    script = directory / f"{name}.py"
    script.write_text(source, encoding="utf-8")
    if os.name == "nt":
        executable = directory / f"{name}.cmd"
        executable.write_text(
            f'@"{sys.executable}" "{script}" %*\n',
            encoding="utf-8",
        )
        return executable
    executable = directory / name
    executable.write_text(f"#!{sys.executable}\n{source}", encoding="utf-8")
    executable.chmod(0o755)
    return executable


def test_langgraph_launcher_needs_no_shell_and_preserves_host_argv(rendered_mcp: Path, tmp_path: Path) -> None:
    lifecycle = tomllib.loads((rendered_mcp / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8"))
    command = lifecycle["processes"]["langgraph"]["command"]
    capture_path = tmp_path / "argv.json"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_python_command(
        fake_bin,
        "uv",
        "import os, sys\n"
        "arguments = sys.argv[1:]\n"
        "if arguments[:2] != ['run', 'python']:\n"
        "    raise SystemExit(f'unexpected uv arguments: {arguments!r}')\n"
        "os.execv(sys.executable, [sys.executable, *arguments[2:]])\n",
    )
    _write_python_command(
        fake_bin,
        "langgraph",
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['ARGV_CAPTURE']).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n",
    )
    hostile_host = "127.0.0.1 --allow-blocking *.json"
    environment = {
        **os.environ,
        "ARGV_CAPTURE": str(capture_path),
        "LANGGRAPH_HOST": hostile_host,
        "PATH": str(fake_bin),
        "PYTHONPATH": str(rendered_mcp / "src"),
    }
    executable = shutil.which(command[0], path=environment["PATH"])
    if executable is None:
        pytest.fail(f"lifecycle depends on unavailable executable: {command[0]}")

    completed = subprocess.run(  # noqa: S603 - executes rendered lifecycle through a controlled fake uv
        [executable, *command[1:]],
        cwd=rendered_mcp,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(capture_path.read_text(encoding="utf-8")) == [
        "dev",
        "--port",
        "2024",
        "--no-browser",
        "--host",
        hostile_host,
    ]


def test_load_mcp_config_normalizes_stdio_and_http(rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_rendered_module(rendered_mcp, "config")
    monkeypatch.setenv("MCP_TOKEN", "secret-token")
    config_path = rendered_mcp / "connections.json"
    config_path.write_text(
        json.dumps({
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
        }),
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

    with pytest.raises(
        module.MCPConfigError, match=r"absolute http or https URL at \$\.mcpServers\.remote\.url"
    ) as exc:
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

    with pytest.raises(
        module.MCPConfigError, match=r"absolute http or https URL at \$\.mcpServers\.remote\.url"
    ) as exc:
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


def test_rendered_calculator_mcp_smoke_is_real(rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(rendered_mcp)
    source_root = rendered_mcp / "src"
    monkeypatch.syspath_prepend(str(source_root))
    monkeypatch.setenv("PYTHONPATH", str(source_root))
    # Production runs `agentseek task sync`, which installs the package. This
    # uninstalled test fixture instead forwards its temporary source tree to
    # the MCP SDK's deliberately restricted stdio subprocess environment.
    http_port = _configure_calculator_http_port(rendered_mcp)
    config_path = rendered_mcp / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["mcpServers"]["calculator"]["env"] = {"PYTHONPATH": "${PYTHONPATH}"}
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    smoke = import_rendered_package_module(rendered_mcp, "mcp_smoke")

    result = asyncio.run(smoke.run_smoke(config_path))

    assert result.tool_names == (
        "calculator_add",
        "calculator_multiply",
        "calculator_http_add",
        "calculator_http_multiply",
    )
    assert result.required_arguments == ("a", "b")
    assert result.stdio_calculation == "95"
    assert result.http_calculation == "2146"
    assert not _loopback_port_is_open(http_port)


def test_http_smoke_child_environment_excludes_application_secrets(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_calculator_http_port(rendered_mcp)
    smoke = import_rendered_package_module(rendered_mcp, "mcp_smoke")
    config = smoke.load_mcp_config(rendered_mcp / ".mcp.json")
    runtime_temp = str(rendered_mcp / "runtime-tmp")
    captured: dict[str, object] = {}

    class ProcessLaunchCaptured(Exception):
        pass

    async def capture_process_launch(*_args: object, **kwargs: object) -> None:
        captured.update(kwargs)
        raise ProcessLaunchCaptured

    monkeypatch.setattr(smoke.asyncio, "create_subprocess_exec", capture_process_launch)
    monkeypatch.setattr(
        smoke.os,
        "environ",
        {
            "APPDATA": r"C:\Users\runner\AppData\Roaming",
            "HOMEDRIVE": "C:",
            "HOMEPATH": r"\Users\runner",
            "LOCALAPPDATA": r"C:\Users\runner\AppData\Local",
            "PATH": "/trusted/bin",
            "PATHEXT": ".COM;.EXE;.BAT;.CMD",
            "PROCESSOR_ARCHITECTURE": "AMD64",
            "PYTHONPATH": "/project/src",
            "SYSTEMDRIVE": "C:",
            "SYSTEMROOT": r"C:\Windows",
            "TEMP": r"C:\Users\runner\AppData\Local\Temp",
            "TMPDIR": runtime_temp,
            "USERNAME": "runner",
            "USERPROFILE": r"C:\Users\runner",
            "AGENTSEEK_MODEL_API_KEY": "model-secret",
            "LANGSMITH_API_KEY": "trace-secret",
            "BILLING_MCP_TOKEN": "tool-secret",
        },
    )

    async def launch_http_server() -> None:
        async with smoke._ensure_calculator_http_server(config):
            pytest.fail("captured process launch unexpectedly yielded")

    with pytest.raises(ProcessLaunchCaptured):
        asyncio.run(launch_http_server())

    assert captured["env"] == {
        "APPDATA": r"C:\Users\runner\AppData\Roaming",
        "HOMEDRIVE": "C:",
        "HOMEPATH": r"\Users\runner",
        "LOCALAPPDATA": r"C:\Users\runner\AppData\Local",
        "PATH": "/trusted/bin",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PROCESSOR_ARCHITECTURE": "AMD64",
        "PYTHONPATH": "/project/src",
        "SYSTEMDRIVE": "C:",
        "SYSTEMROOT": r"C:\Windows",
        "TEMP": r"C:\Users\runner\AppData\Local\Temp",
        "TMPDIR": runtime_temp,
        "USERNAME": "runner",
        "USERPROFILE": r"C:\Users\runner",
    }


def test_smoke_reuses_running_http_server_without_stopping_it(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(rendered_mcp)
    source_root = rendered_mcp / "src"
    monkeypatch.syspath_prepend(str(source_root))
    monkeypatch.setenv("PYTHONPATH", str(source_root))
    http_port = _configure_calculator_http_port(rendered_mcp)
    config_path = rendered_mcp / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["mcpServers"]["calculator"]["env"] = {"PYTHONPATH": "${PYTHONPATH}"}
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    smoke = import_rendered_package_module(rendered_mcp, "mcp_smoke")
    process = subprocess.Popen(  # noqa: S603 - current interpreter and rendered trusted module
        [
            sys.executable,
            "-m",
            f"{rendered_mcp.name}.calculator_http_server",
            "--host",
            "127.0.0.1",
            "--port",
            str(http_port),
        ],
        cwd=rendered_mcp,
        env={**os.environ, "PYTHONPATH": str(source_root)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_loopback_port(http_port)

        result = asyncio.run(smoke.run_smoke(config_path))

        assert result.http_calculation == "2146"
        assert process.poll() is None
        assert _loopback_port_is_open(http_port)
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_command_only_stdio_connection_discovers_real_mcp_tools(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(rendered_mcp)
    source_root = rendered_mcp / "src"
    monkeypatch.syspath_prepend(str(source_root))
    monkeypatch.setenv("PYTHONPATH", str(source_root))
    launcher = _write_python_command(
        rendered_mcp,
        "calculator-mcp",
        f'from {rendered_mcp.name}.calculator_server import mcp\nmcp.run(transport="stdio")\n',
    )
    config_path = write_json(
        rendered_mcp,
        {
            "mcpServers": {
                "calculator": {
                    "transport": "stdio",
                    "command": str(launcher),
                    "env": {"PYTHONPATH": "${PYTHONPATH}"},
                }
            }
        },
    )
    config_module = import_rendered_package_module(rendered_mcp, "config")
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")

    loaded = config_module.load_mcp_config(config_path)
    discovered = asyncio.run(tools_module.load_mcp_tools(loaded))

    assert loaded.servers["calculator"]["args"] == []
    assert discovered.tool_names == ("calculator_add", "calculator_multiply")


@pytest.mark.parametrize(
    ("dotenv_uses_source", "exported_uses_source"),
    [(True, False), (False, True)],
    ids=["dotenv-only", "exported-environment-precedence"],
)
def test_real_mcp_smoke_loads_project_dotenv_without_overriding_exported_values(
    rendered_mcp: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    dotenv_uses_source: bool,
    exported_uses_source: bool,
) -> None:
    monkeypatch.chdir(rendered_mcp)
    for name in (
        "AGENTSEEK_MODEL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    source_root = rendered_mcp / "src"
    monkeypatch.syspath_prepend(str(source_root))
    # The rendered package is not installed in this fixture, so the HTTP
    # subprocess needs the same source-root forwarding as the stdio subprocess.
    monkeypatch.setenv("PYTHONPATH", str(source_root))
    _configure_calculator_http_port(rendered_mcp)
    variable = "MCP_SMOKE_PYTHONPATH"
    invalid_path = tmp_path / "invalid-pythonpath"
    dotenv_value = source_root if dotenv_uses_source else invalid_path
    (rendered_mcp / ".env").write_text(f"{variable}={dotenv_value}\n", encoding="utf-8")
    if exported_uses_source:
        monkeypatch.setenv(variable, str(source_root))
    else:
        monkeypatch.delenv(variable, raising=False)

    config_path = rendered_mcp / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["mcpServers"]["calculator"]["env"] = {
        "PYTHONPATH": f"${{{variable}}}",
    }
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    smoke = import_rendered_package_module(rendered_mcp, "mcp_smoke")

    try:
        result = asyncio.run(smoke.run_smoke(config_path))
    finally:
        os.environ.pop(variable, None)

    assert result.tool_names == (
        "calculator_add",
        "calculator_multiply",
        "calculator_http_add",
        "calculator_http_multiply",
    )
    assert result.required_arguments == ("a", "b")
    assert result.stdio_calculation == "95"
    assert result.http_calculation == "2146"


def test_rendered_calculator_mcp_smoke_cli_runs_the_real_check(rendered_mcp: Path) -> None:
    environment, http_port = prepare_rendered_mcp_subprocess(rendered_mcp)

    result = subprocess.run(  # noqa: S603 - executes the current trusted interpreter
        [sys.executable, "-m", f"{rendered_mcp.name}.mcp_smoke"],
        cwd=rendered_mcp,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "MCP smoke check passed: "
        "tools=calculator_add,calculator_multiply,calculator_http_add,calculator_http_multiply; "
        "required_arguments=a,b; stdio_calculation=95; http_calculation=2146\n"
    )
    assert not _loopback_port_is_open(http_port)


def test_rendered_calculator_mcp_smoke_cli_fails_on_smoke_check_error(rendered_mcp: Path) -> None:
    environment, http_port = prepare_rendered_mcp_subprocess(rendered_mcp, server_name="unexpected")

    result = subprocess.run(  # noqa: S603 - executes the current trusted interpreter
        [sys.executable, "-m", f"{rendered_mcp.name}.mcp_smoke"],
        cwd=rendered_mcp,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "SmokeCheckError: Calculator MCP exposed unexpected tool names." in result.stderr
    assert not _loopback_port_is_open(http_port)


def test_mcp_discovery_failure_does_not_leak_underlying_secret(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")

    class SecretFailingClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[object]:
            if server_name == "private":
                raise RuntimeError(  # noqa: TRY003 - deliberate secret-bearing dependency failure
                    "Authorization failed for Bearer secret-token"
                )
            return [SimpleNamespace(name="healthy_ping")]

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", SecretFailingClient)
    config = config_module.MCPConfig(
        servers={
            "healthy": {"transport": "stdio", "command": "python"},
            "private": {"transport": "stdio", "command": "python"},
        }
    )

    with pytest.raises(tools_module.MCPDiscoveryError, match="server 'private'") as exc:
        asyncio.run(tools_module.load_mcp_tools(config))

    assert "secret-token" not in str(exc.value)


def test_zero_tool_server_rejects_the_entire_discovery_result(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")

    class ZeroToolClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[object]:
            if server_name == "empty":
                return []
            return [SimpleNamespace(name="healthy_ping")]

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", ZeroToolClient)
    config = config_module.MCPConfig(
        servers={
            "empty": {"transport": "stdio", "command": "python"},
            "healthy": {"transport": "stdio", "command": "python"},
        }
    )

    with pytest.raises(tools_module.MCPDiscoveryError, match="server 'empty' exposed no tools"):
        asyncio.run(tools_module.load_mcp_tools(config))


def test_failed_discovery_finalizes_siblings_before_error_and_retry(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")
    events: list[str] = []
    client_attempts = 0

    class CancellingClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            nonlocal client_attempts
            client_attempts += 1
            self.attempt = client_attempts
            self.slow_started = asyncio.Event()

        async def get_tools(self, *, server_name: str) -> list[object]:
            if self.attempt > 1:
                return [SimpleNamespace(name=f"{server_name}_ping")]
            if server_name == "a_fail":
                await self.slow_started.wait()
                raise RuntimeError("failure contains secret-token")  # noqa: TRY003
            events.append("slow-started")
            self.slow_started.set()
            try:
                await asyncio.Event().wait()
            finally:
                events.append("slow-finalized")
            raise AssertionError("slow server unexpectedly resumed")  # noqa: TRY003

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", CancellingClient)
    config = config_module.MCPConfig(
        servers={
            "a_fail": {"transport": "stdio", "command": "python"},
            "z_slow": {"transport": "stdio", "command": "python"},
        }
    )

    async def fail_then_retry() -> object:
        with pytest.raises(tools_module.MCPDiscoveryError, match="server 'a_fail'") as exc:
            await tools_module.load_mcp_tools(config)
        assert "secret-token" not in str(exc.value)
        assert events == ["slow-started", "slow-finalized"]
        events.append("retry-started")
        return await tools_module.load_mcp_tools(config)

    loaded = cast(_LoadedToolsLike, asyncio.run(fail_then_retry()))

    assert events == ["slow-started", "slow-finalized", "retry-started"]
    assert loaded.tool_names == ("a_fail_ping", "z_slow_ping")


def test_duplicate_final_mcp_names_identify_both_server_tool_pairs(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")

    class DuplicateNameClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[object]:
            return [SimpleNamespace(name="a_b_c", description="secret-token")]

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", DuplicateNameClient)
    config = config_module.MCPConfig(
        servers={
            "a": {"transport": "stdio", "command": "python"},
            "a_b": {"transport": "stdio", "command": "python"},
        }
    )

    with pytest.raises(
        tools_module.MCPDiscoveryError,
        match=r"server/tool pairs 'a'/'b_c' and 'a_b'/'c'",
    ) as exc:
        asyncio.run(tools_module.load_mcp_tools(config))

    assert "secret-token" not in str(exc.value)


def test_mcp_name_cannot_collide_with_enabled_deepagents_builtin(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")

    class BuiltinCollisionClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[object]:
            return [SimpleNamespace(name="write_todos", description="secret-token")]

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", BuiltinCollisionClient)
    config = config_module.MCPConfig(servers={"write": {"transport": "stdio", "command": "python"}})

    with pytest.raises(
        tools_module.MCPDiscoveryError,
        match=r"server/tool pair 'write'/'todos'.*enabled DeepAgents built-in",
    ) as exc:
        asyncio.run(tools_module.load_mcp_tools(config))

    assert "secret-token" not in str(exc.value)


def test_reserved_mcp_names_match_real_deepagents_0_6_12_runtime(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deepagents._version import __version__ as deepagents_version

    assert deepagents_version == CHARACTERIZED_DEEPAGENTS_VERSION, (
        "repository test environment must exercise the exact DeepAgents runtime pinned by the generated template"
    )

    from deepagents import (
        GeneralPurposeSubagentProfile,
        HarnessProfile,
        create_deep_agent,
        register_harness_profile,
    )
    from langchain_openai import ChatOpenAI

    tools_module = import_rendered_package_module(rendered_mcp, "mcp_tools")
    config_module = importlib.import_module(f"{rendered_mcp.name}.config")
    profile_key = "openai:mcp-final-name-regression"
    register_harness_profile(
        profile_key,
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    graph = create_deep_agent(
        model=ChatOpenAI(model="mcp-final-name-regression", api_key=SecretStr("unused-test-key")),
        tools=[],
        subagents=[],
    )
    tool_node = cast(_ToolNodeLike, graph.nodes["tools"])

    assert frozenset(tool_node.bound.tools_by_name) == tools_module.RESERVED_DEEPAGENTS_TOOL_NAMES
    assert "task" not in tools_module.RESERVED_DEEPAGENTS_TOOL_NAMES

    class ExternalWriteTodosClient:
        def __init__(self, connections: object, **kwargs: object) -> None:
            pass

        async def get_tools(self, *, server_name: str) -> list[object]:
            return [SimpleNamespace(name="write_todos", description="EXTERNAL MCP COLLISION SENTINEL")]

    monkeypatch.setattr(tools_module, "MultiServerMCPClient", ExternalWriteTodosClient)
    config = config_module.MCPConfig(servers={"write": {"transport": "stdio", "command": "python"}})
    with pytest.raises(tools_module.MCPDiscoveryError, match="enabled DeepAgents built-in"):
        asyncio.run(tools_module.load_mcp_tools(config))

    builtin = cast(_DescribedToolLike, tool_node.bound.tools_by_name["write_todos"])
    assert builtin.description != "EXTERNAL MCP COLLISION SENTINEL"


def test_model_environment_precedence_and_provider_native_settings(
    rendered_mcp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_module = load_rendered_module(rendered_mcp, "model")
    for name in (
        "AGENTSEEK_MODEL",
        "DEEPAGENTS_MODEL",
        "BUB_MODEL",
        "AGENTSEEK_MODEL_PROVIDER",
        "GOOGLE_API_KEY",
        "GOOGLE_API_BASE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("BUB_MODEL", "fallback-model")
    monkeypatch.setenv("DEEPAGENTS_MODEL", "compat-model")
    monkeypatch.setenv("AGENTSEEK_MODEL", "primary-model")
    monkeypatch.setenv("AGENTSEEK_MODEL_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("GOOGLE_API_BASE", "https://google.example.com")
    captured: dict[str, object] = {}

    def fake_init_chat_model(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(model_module, "init_chat_model", fake_init_chat_model)

    built = model_module.build_model()

    assert built is not None
    assert captured == {
        "model": "primary-model",
        "model_provider": "google_genai",
        "api_key": "google-key",
        "base_url": "https://google.example.com",
    }
    assert model_module.model_profile_key() == "google_genai:primary-model"


@pytest.mark.parametrize(
    ("provider", "model_name", "expected_type", "key_attribute", "base_name", "base_value"),
    [
        ("openai", "gpt-local", "ChatOpenAI", "openai_api_key", "OPENAI_API_BASE", "https://openai.local/v1"),
        (
            "anthropic",
            "claude-local",
            "ChatAnthropic",
            "anthropic_api_key",
            "ANTHROPIC_API_URL",
            "https://anthropic.local",
        ),
        (
            "google_genai",
            "gemini-local",
            "ChatGoogleGenerativeAI",
            "google_api_key",
            "GOOGLE_API_BASE",
            "https://google.local",
        ),
    ],
)
def test_shared_model_key_constructs_selected_real_provider_without_hosted_call(
    rendered_mcp: Path,
    provider: str,
    model_name: str,
    expected_type: str,
    key_attribute: str,
    base_name: str,
    base_value: str,
) -> None:
    model_module = load_rendered_module(rendered_mcp, "model")
    binding = model_module.resolve_model_binding({
        "AGENTSEEK_MODEL_PROVIDER": provider,
        "AGENTSEEK_MODEL": model_name,
        "AGENTSEEK_MODEL_API_KEY": "shared-test-key",
        {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google_genai": "GOOGLE_API_KEY",
        }[provider]: "wrong-native-key",
        base_name: base_value,
    })

    credential = getattr(binding.model, key_attribute)
    assert type(binding.model).__name__ == expected_type
    assert credential.get_secret_value() == "shared-test-key"
    assert binding.profile_key == f"{provider}:{model_name}"


@pytest.mark.parametrize(
    ("provider", "mismatched_key"),
    [
        ("openai", "ANTHROPIC_API_KEY"),
        ("openai", "GOOGLE_API_KEY"),
        ("anthropic", "OPENAI_API_KEY"),
        ("anthropic", "GOOGLE_API_KEY"),
        ("google_genai", "OPENAI_API_KEY"),
        ("google_genai", "ANTHROPIC_API_KEY"),
    ],
)
def test_public_doctor_requires_shared_key_for_every_provider(
    rendered_mcp: Path, provider: str, mismatched_key: str
) -> None:
    (rendered_mcp / "frontend" / "node_modules").mkdir()
    (rendered_mcp / ".env").write_text("", encoding="utf-8")
    environment = dict(os.environ)
    for name in (
        "AGENTSEEK_MODEL_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
    ):
        environment.pop(name, None)
    environment.update({
        "AGENTSEEK_MODEL_PROVIDER": provider,
        "AGENTSEEK_MODEL": "local-constructor-only",
    })
    environment[mismatched_key] = "wrong-provider-key"

    mismatched = subprocess.run(
        [sys.executable, "-m", "agentseek", "doctor"],
        cwd=rendered_mcp,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert mismatched.returncode == 1
    assert "AGENTSEEK_MODEL_API_KEY is not configured" in mismatched.stdout

    environment["AGENTSEEK_MODEL_API_KEY"] = "shared-test-key"
    matching = subprocess.run(
        [sys.executable, "-m", "agentseek", "doctor"],
        cwd=rendered_mcp,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert matching.returncode == 0, matching.stdout + matching.stderr
    assert "AGENTSEEK_MODEL_API_KEY is configured" in matching.stdout


def test_langgraph_file_export_loads_under_a_synthetic_module_name(
    rendered_mcp: Path, rendered_agent: ModuleType
) -> None:
    config = json.loads((rendered_mcp / "langgraph.json").read_text(encoding="utf-8"))
    source, export_name = config["graphs"]["mcp"].split(":", maxsplit=1)
    source_path = rendered_mcp / source
    spec = importlib.util.spec_from_file_location("langgraph_api_graph_1234", source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.modules[spec.name]

    exported = getattr(module, export_name)
    assert inspect.iscoroutinefunction(exported)


def test_invalid_model_fails_before_mcp_discovery(rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    config = object()

    def load_config(path: Path) -> object:
        assert path == Path(".mcp.json")
        events.append("config")
        return config

    def invalid_model() -> object:
        events.append("model")
        raise ValueError("bad model")  # noqa: TRY003 - deliberate model validation failure

    async def load_tools(_config: object) -> object:
        events.append("discover")
        return object()

    monkeypatch.setattr(rendered_agent, "load_mcp_config", load_config)
    monkeypatch.setattr(rendered_agent, "resolve_model_binding", invalid_model)
    monkeypatch.setattr(rendered_agent, "load_mcp_tools", load_tools)

    with pytest.raises(ValueError, match="bad model"):
        asyncio.run(rendered_agent.make_graph())

    assert events == ["config", "model"]


def test_runtime_loads_project_mcp_config_and_registers_model_specific_profile(
    rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    graph = SimpleNamespace(tool_names=())
    model = object()
    tool = SimpleNamespace(name="calculator_add")
    client = object()
    registered: list[tuple[str, _HarnessProfileLike]] = []
    created: list[dict[str, object]] = []

    def load_config(path: Path) -> object:
        assert path == Path(".mcp.json")
        return object()

    async def load_tools(_config: object) -> object:
        return SimpleNamespace(client=client, tools=(tool,), tool_names=(tool.name,))

    def register_profile(key: str, profile: object) -> None:
        registered.append((key, cast(_HarnessProfileLike, profile)))

    def create_agent(**kwargs: object) -> object:
        created.append(kwargs)
        key, profile = registered[-1]
        general_purpose_subagent = profile.general_purpose_subagent
        subagents = kwargs["subagents"]
        tools_value = kwargs["tools"]
        assert key == "openai:gpt-test"
        assert general_purpose_subagent.enabled is False
        assert isinstance(subagents, list)
        assert subagents == []
        assert isinstance(tools_value, list)
        tools = cast(list[_NamedTool], tools_value)
        exposed_names = {item.name for item in tools}
        if general_purpose_subagent.enabled is not False or subagents:
            exposed_names.add("task")
        graph.tool_names = tuple(sorted(exposed_names))
        return graph

    monkeypatch.setattr(rendered_agent, "load_mcp_config", load_config)
    monkeypatch.setattr(
        rendered_agent,
        "resolve_model_binding",
        lambda: SimpleNamespace(model=model, profile_key="openai:gpt-test"),
    )
    monkeypatch.setattr(rendered_agent, "load_mcp_tools", load_tools)
    monkeypatch.setattr(rendered_agent, "register_harness_profile", register_profile)
    monkeypatch.setattr(rendered_agent, "create_deep_agent", create_agent)

    bundle = asyncio.run(rendered_agent._build_runtime())

    assert bundle.client is client
    assert bundle.tool_names == ("calculator_add",)
    assert bundle.graph is graph
    assert "task" not in bundle.graph.tool_names
    assert len(registered) == 1
    assert len(created) == 1


def test_runtime_profile_key_cannot_drift_during_discovery(
    rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENTSEEK_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("AGENTSEEK_MODEL", "gpt-before-discovery")
    monkeypatch.setenv("OPENAI_API_KEY", "unused-test-key")

    async def mutate_environment(_config: object) -> object:
        monkeypatch.setenv("AGENTSEEK_MODEL", "gpt-after-discovery")
        tool = SimpleNamespace(name="calculator_add")
        return SimpleNamespace(client=object(), tools=(tool,), tool_names=(tool.name,))

    registrations: list[str] = []
    created_models: list[_NamedModel] = []
    graph = object()

    def create_agent(**kwargs: object) -> object:
        created_models.append(cast(_NamedModel, kwargs["model"]))
        return graph

    monkeypatch.setattr(rendered_agent, "load_mcp_config", lambda _path: object())
    monkeypatch.setattr(rendered_agent, "load_mcp_tools", mutate_environment)
    monkeypatch.setattr(rendered_agent, "register_harness_profile", lambda key, _profile: registrations.append(key))
    monkeypatch.setattr(rendered_agent, "create_deep_agent", create_agent)

    bundle = asyncio.run(rendered_agent._build_runtime())

    assert bundle.graph is graph
    assert registrations == ["openai:gpt-before-discovery"]
    assert len(created_models) == 1
    assert created_models[0].model_name == "gpt-before-discovery"
    assert type(created_models[0]).__name__ == "ChatOpenAI"
    assert os.environ["AGENTSEEK_MODEL"] == "gpt-after-discovery"


def test_colon_bearing_native_model_is_rejected_before_model_or_discovery(
    rendered_mcp: Path, rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_module = importlib.import_module(f"{rendered_mcp.name}.model")
    sensitive_model = "ft:gpt-private-org:secret-job"
    events: list[str] = []
    monkeypatch.setenv("AGENTSEEK_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("AGENTSEEK_MODEL", sensitive_model)

    def construct_model(**_kwargs: object) -> object:
        events.append("model")
        return object()

    async def discover(_config: object) -> object:
        events.append("discover")
        tool = SimpleNamespace(name="calculator_add")
        return SimpleNamespace(client=object(), tools=(tool,), tool_names=(tool.name,))

    def validate_registry_key(key: str, _profile: object) -> None:
        if key.count(":") > 1:
            raise ValueError(  # noqa: TRY003 - mirrors DeepAgents 0.6.12 key validation
                f"Profile key {key!r} has more than one ':'; expected 'provider' or 'provider:model'."
            )

    monkeypatch.setattr(model_module, "init_chat_model", construct_model)
    monkeypatch.setattr(rendered_agent, "load_mcp_config", lambda _path: object())
    monkeypatch.setattr(rendered_agent, "load_mcp_tools", discover)
    monkeypatch.setattr(rendered_agent, "register_harness_profile", validate_registry_key)

    with pytest.raises(ValueError, match="more than one ':'") as exc:
        asyncio.run(rendered_agent._build_runtime())

    assert sensitive_model not in str(exc.value)
    assert events == []


def test_concurrent_graph_factory_builds_one_runtime(
    rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    builds = 0
    graph = object()

    async def build_once() -> object:
        nonlocal builds
        builds += 1
        await asyncio.sleep(0)
        return SimpleNamespace(graph=graph)

    monkeypatch.setattr(rendered_agent, "_build_runtime", build_once)

    async def call_twice() -> tuple[object, object]:
        first, second = await asyncio.gather(rendered_agent.make_graph(), rendered_agent.make_graph())
        return first, second

    first, second = asyncio.run(call_twice())

    assert first is graph
    assert second is graph
    assert first is second
    assert builds == 1


def test_graph_factory_retries_after_failed_runtime_build(
    rendered_agent: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = 0
    graph = object()

    async def fail_once() -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary startup failure")  # noqa: TRY003 - deliberate retry trigger
        return SimpleNamespace(graph=graph)

    monkeypatch.setattr(rendered_agent, "_build_runtime", fail_once)

    with pytest.raises(RuntimeError, match="temporary startup failure"):
        asyncio.run(rendered_agent.make_graph())

    assert asyncio.run(rendered_agent.make_graph()) is graph
    assert attempts == 2


def _fenced_blocks(markdown: str, language: str) -> list[str]:
    pattern = rf"```{re.escape(language)}\n(.*?)\n```"
    return re.findall(pattern, markdown, flags=re.DOTALL)


def _normalized(markdown: str) -> str:
    return " ".join(markdown.split())


def _assert_mcp_json_examples(markdown: str) -> None:
    blocks = _fenced_blocks(markdown, "json")
    assert blocks
    connections: list[dict[str, object]] = []
    for block in blocks:
        parsed = json.loads(block)
        assert isinstance(parsed, dict)
        servers = parsed.get("mcpServers")
        assert isinstance(servers, dict) and servers
        for connection in servers.values():
            assert isinstance(connection, dict)
            connections.append(connection)

    assert all(connection.get("transport") in {"stdio", "http"} for connection in connections)
    stdio = [connection for connection in connections if connection.get("transport") == "stdio"]
    http = [connection for connection in connections if connection.get("transport") == "http"]
    assert stdio and http
    assert any(
        connection.get("command") == "${PYTHON_EXECUTABLE}"
        and isinstance(connection.get("args"), list)
        and isinstance(connection.get("env"), dict)
        for connection in stdio
    )
    assert any(
        isinstance(connection.get("url"), str)
        and str(connection["url"]).startswith("${")
        and isinstance(connection.get("headers"), dict)
        for connection in http
    )


def _assert_hitl_policy(markdown: str) -> None:
    policies: list[object] = []
    for block in _fenced_blocks(markdown, "python"):
        module = ast.parse(block)
        for statement in module.body:
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == "interrupt_on"
            ):
                policies.append(ast.literal_eval(statement.value))
    assert policies == [{"billing_charge_card": {"allowed_decisions": ["approve", "reject"]}}]


def test_mcp_template_readmes_cover_runtime_contract(rendered_mcp: Path) -> None:
    source = (TEMPLATE / "README.md").read_text(encoding="utf-8")
    generated = (rendered_mcp / "README.md").read_text(encoding="utf-8")
    normalized_source = _normalized(source)
    normalized_generated = _normalized(generated)

    expected_commands = [
        "cp .env.example .env",
        "cp frontend/.env.example frontend/.env",
        "uvx agentseek task sync",
        "uvx agentseek task frontend",
        "uvx agentseek task mcp-smoke",
        "uvx agentseek info",
        "uvx agentseek doctor",
        "uvx agentseek dev --dry-run",
        "uvx agentseek dev",
    ]
    bash_blocks = _fenced_blocks(generated, "bash")
    assert bash_blocks[0].splitlines() == expected_commands[:2]
    assert bash_blocks[1].splitlines() == expected_commands[2:]
    first_block_start = generated.index("```bash")
    first_block_end = generated.index("```", first_block_start + len("```bash"))
    edit_instruction = generated.index("Edit `.env`")
    second_block_start = generated.index("```bash", first_block_end + len("```"))
    assert first_block_end < edit_instruction < second_block_start
    documented_commands = [line for block in bash_blocks for line in block.splitlines() if line in expected_commands]
    assert documented_commands == expected_commands

    for text in (source, generated):
        _assert_mcp_json_examples(text)
        _assert_hitl_policy(text)

    common_clauses = [
        "`${ENV_VAR}` references are interpolated in commands, arguments, environment values, URLs, and headers. Every reference must resolve.",
        "`${PYTHON_EXECUTABLE}` is reserved and always resolves to the current Python interpreter. An environment variable named `PYTHON_EXECUTABLE` cannot override it.",
        "Every configured server must connect and expose at least one tool. If any server fails or returns no tools, graph creation fails without a partial tool set.",
        "Restart the AgentSeek development processes after changing `.mcp.json`, model settings, or server credentials.",
        "MCP tool calls are stateless and do not retain persistent MCP client sessions between calls.",
        "Adding, removing, or replacing any server changes the complete discovered tool-name tuple, so update the calculator smoke contract at the same time.",
        "Final names must be unique and cannot replace the enabled DeepAgents built-ins:",
        "The `task` tool is disabled by this template's harness profile and is not reserved.",
        "This template pins DeepAgents to `0.6.12` because the enabled built-in tool set and harness profile APIs are characterized for that exact runtime.",
        "Before upgrading DeepAgents, rerun and update the real built-in collision characterization, reserved-name set, and profile regressions together.",
        "Set `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` for the DeepAgents graph. `DEEPAGENTS_MODEL` and `BUB_MODEL` are model-name compatibility aliases.",
        "`AGENTSEEK_MODEL_API_KEY` is",
        "Provider-native API keys remain",
        "they do not satisfy",
        "Optional custom endpoints continue to use the provider-native variables in `.env.example`.",
        "Optional LangSmith tracing uses `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`.",
        "All three development processes bind to loopback by default.",
        "`LANGGRAPH_HOST` controls LangGraph from the launching shell. `FRONTEND_HOST` controls Vite from that shell or `frontend/.env`.",
        "set `VITE_LANGGRAPH_API_URL` in `frontend/.env` to the public LangGraph API URL.",
        "Keep MCP URLs, headers, and credentials out of Vite variables.",
        "This v1 template exposes MCP Tools only. It does not expose MCP Resources or Prompts, persistent MCP client sessions, interceptors, OAuth helpers, or a browser-based MCP configuration editor.",
        "Treat every configured `stdio` command as trusted local code execution.",
        "TLS, network ACLs, and authentication or OAuth must be enforced at the MCP server, gateway, or deployment boundary.",
        "MCP tool descriptions and annotations do not authorize calls.",
        "This example does not enable automatic HITL.",
        "Keep secrets in the process environment or the untracked `.env` file and reference them from `.mcp.json` with `${ENV_VAR}`.",
        "The root `.env` file is loaded by both `agentseek task mcp-smoke` and `agentseek dev`, while exported process values take precedence.",
        "Never put secret literals in tracked `.mcp.json`, commits, logs, error messages, shell output, or shared output, and never echo them.",
        "Do not rely on the template to redact arbitrary MCP tool error content.",
    ]
    for normalized in (normalized_source, normalized_generated):
        for clause in common_clauses:
            assert clause in normalized
        assert "persistent sessions" not in normalized
    assert "LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 uvx agentseek dev" in generated
    assert "Optional installed-CLI shortcut" in generated

    english_description = (
        "DeepAgents MCP Tools app with validated stdio/HTTP configuration, a local calculator example, "
        "streamed UI, and AgentSeek lifecycle spec."
    )
    english_row = f"| `deepagents/mcp` | {english_description} |"
    chinese_row = (
        "| `deepagents/mcp` | DeepAgents MCP Tools 应用，提供经过校验的 stdio/HTTP 配置、"  # noqa: RUF001
        "本地计算器示例、流式 UI 和 AgentSeek 生命周期规范。 |"
    )
    assert english_row in (REPO_ROOT / "docs" / "reference" / "templates.md").read_text(encoding="utf-8")
    assert chinese_row in (REPO_ROOT / "docs" / "reference" / "templates.zh.md").read_text(encoding="utf-8")
    registry = json.loads((REPO_ROOT / "templates" / "index.json").read_text(encoding="utf-8"))
    assert registry["deepagents/mcp"] == english_description
