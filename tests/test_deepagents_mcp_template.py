from __future__ import annotations

import asyncio
import importlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace

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


def prepare_rendered_mcp_subprocess(rendered: Path, *, server_name: str = "calculator") -> dict[str, str]:
    source_root = rendered / "src"
    config_path = rendered / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    calculator = config_payload["mcpServers"].pop("calculator")
    calculator["env"] = {"PYTHONPATH": "${PYTHONPATH}"}
    config_payload["mcpServers"][server_name] = calculator
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    return {**os.environ, "PYTHONPATH": str(source_root)}


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
    config_path = rendered_mcp / ".mcp.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["mcpServers"]["calculator"]["env"] = {"PYTHONPATH": "${PYTHONPATH}"}
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")
    smoke = importlib.import_module(f"{rendered_mcp.name}.mcp_smoke")

    result = asyncio.run(smoke.run_smoke(config_path))

    assert result.tool_names == ("calculator_add", "calculator_multiply")
    assert result.required_arguments == ("a", "b")
    assert result.calculation == "95"


def test_rendered_calculator_mcp_smoke_cli_runs_the_real_check(rendered_mcp: Path) -> None:
    environment = prepare_rendered_mcp_subprocess(rendered_mcp)

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
        "MCP smoke check passed: tools=calculator_add,calculator_multiply; required_arguments=a,b; calculation=95\n"
    )


def test_rendered_calculator_mcp_smoke_cli_fails_on_smoke_check_error(rendered_mcp: Path) -> None:
    environment = prepare_rendered_mcp_subprocess(rendered_mcp, server_name="unexpected")

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
    registered: list[tuple[str, object]] = []
    created: list[dict[str, object]] = []

    def load_config(path: Path) -> object:
        assert path == Path(".mcp.json")
        return object()

    async def load_tools(_config: object) -> object:
        return SimpleNamespace(client=client, tools=(tool,), tool_names=(tool.name,))

    def register_profile(key: str, profile: object) -> None:
        registered.append((key, profile))

    def create_agent(**kwargs: object) -> object:
        created.append(kwargs)
        key, profile = registered[-1]
        assert key == "openai:gpt-test"
        assert profile.general_purpose_subagent.enabled is False
        assert kwargs["subagents"] == []
        exposed_names = {item.name for item in kwargs["tools"]}
        if profile.general_purpose_subagent.enabled is not False or kwargs["subagents"]:
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
    created_models: list[object] = []
    graph = object()

    def create_agent(**kwargs: object) -> object:
        created_models.append(kwargs["model"])
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
