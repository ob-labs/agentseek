from __future__ import annotations

import ast
import asyncio
import importlib
import importlib.util
import json
import sys
import threading
import tomllib
import types
import warnings
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "deepagents" / "sandbox"


@pytest.fixture
def rendered_sandbox(tmp_path: Path) -> Path:
    output = tmp_path / "rendered"
    output.mkdir()
    cookiecutter(str(TEMPLATE), output_dir=str(output), no_input=True)
    return output / "sandbox_coding_agent"


def _load_sandbox_module(rendered: Path):
    path = rendered / "src" / rendered.name / "sandbox.py"
    spec = importlib.util.spec_from_file_location("rendered_sandbox_provider", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_webapp_module(rendered: Path, monkeypatch: pytest.MonkeyPatch, cleanup_sandbox):
    package_name = rendered.name
    package = types.ModuleType(package_name)
    package.__path__ = [str(rendered / "src" / package_name)]
    agent = types.ModuleType(f"{package_name}.agent")
    agent.__dict__["cleanup_sandbox"] = cleanup_sandbox
    runtime = types.ModuleType(f"{package_name}.runtime")
    runtime.__dict__["cleanup_sandbox"] = cleanup_sandbox

    class FakeFastAPI:
        def __init__(self, *, lifespan):
            self.lifespan = lifespan

    monkeypatch.setitem(sys.modules, package_name, package)
    monkeypatch.setitem(sys.modules, f"{package_name}.agent", agent)
    monkeypatch.setitem(sys.modules, f"{package_name}.runtime", runtime)
    monkeypatch.setitem(sys.modules, "fastapi", types.SimpleNamespace(FastAPI=FakeFastAPI))

    path = rendered / "src" / package_name / "webapp.py"
    spec = importlib.util.spec_from_file_location("rendered_sandbox_webapp", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rendered_dependencies_include_both_sandbox_integrations(rendered_sandbox: Path) -> None:
    project = tomllib.loads((rendered_sandbox / "pyproject.toml").read_text())
    dependencies = project["project"]["dependencies"]
    assert "langchain-daytona>=0.0.7" in dependencies
    assert "langsmith[sandbox]" in dependencies
    assert "fastapi>=0.115" in dependencies


def test_rendered_langgraph_uses_custom_http_app(rendered_sandbox: Path) -> None:
    config = json.loads((rendered_sandbox / "langgraph.json").read_text())
    assert config["http"]["app"] == f"./src/{rendered_sandbox.name}/webapp.py:app"
    assert (rendered_sandbox / "src" / rendered_sandbox.name / "webapp.py").is_file()


def test_rendered_webapp_lifespan_always_invokes_agent_cleanup(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    module = _load_webapp_module(rendered_sandbox, monkeypatch, lambda: events.append("cleanup"))

    class LifespanError(RuntimeError):
        pass

    async def exercise_lifespan() -> None:
        with pytest.raises(LifespanError):
            async with module.app.lifespan(module.app):
                events.append("running")
                raise LifespanError

    asyncio.run(exercise_lifespan())
    assert events == ["running", "cleanup"]


def test_rendered_descriptions_default_to_daytona_and_keep_langsmith_as_an_alternative(
    rendered_sandbox: Path,
) -> None:
    project = tomllib.loads((rendered_sandbox / "pyproject.toml").read_text())
    agent_source = (rendered_sandbox / "src" / rendered_sandbox.name / "agent.py").read_text()
    agent_docstring = ast.get_docstring(ast.parse(agent_source))

    for description in (project["project"]["description"], agent_docstring):
        assert description is not None
        assert "Daytona by default" in description
        assert "LangSmith Sandbox as an alternative" in description


def test_generated_configuration_defaults_to_daytona_and_warns_about_langsmith_charges(
    rendered_sandbox: Path,
) -> None:
    env_text = (rendered_sandbox / ".env.example").read_text()
    lifecycle = tomllib.loads((rendered_sandbox / ".agentseek" / "lifecycle.toml").read_text())
    readme = (rendered_sandbox / "README.md").read_text()

    assert "AGENTSEEK_SANDBOX_PROVIDER=daytona" in env_text
    assert "DAYTONA_API_KEY=" in env_text
    assert "LANGSMITH_API_KEY=" in env_text
    assert "charged" in env_text.lower()
    assert lifecycle["env"]["AGENTSEEK_SANDBOX_PROVIDER"]["default"] == "daytona"
    assert lifecycle["env"]["DAYTONA_API_KEY"]["required"] is False
    assert lifecycle["env"]["LANGSMITH_API_KEY"]["required"] is False
    assert "Daytona" in readme
    assert "LangSmith Sandbox" in readme
    assert "charged" in readme.lower()


def test_template_and_generated_readmes_explain_cleanup_paths(rendered_sandbox: Path) -> None:
    for readme_path in (TEMPLATE / "README.md", rendered_sandbox / "README.md"):
        readme = " ".join(readme_path.read_text().lower().split())
        assert "custom server lifespan" in readme
        assert "atexit" in readme
        assert "cleanup warning" in readme
        assert "provider dashboard" in readme
        assert "process is killed" in readme


def test_provider_normalization(rendered_sandbox: Path) -> None:
    module = _load_sandbox_module(rendered_sandbox)
    assert module.normalize_sandbox_provider("DAYTONA") == "daytona"
    assert module.normalize_sandbox_provider(" langsmith ") == "langsmith"
    with pytest.raises(ValueError, match="daytona, langsmith"):
        module.normalize_sandbox_provider("other")


def test_rendered_runtime_is_the_only_sandbox_resource_owner(rendered_sandbox: Path) -> None:
    agent = (rendered_sandbox / "src" / rendered_sandbox.name / "agent.py").read_text()
    runtime_path = rendered_sandbox / "src" / rendered_sandbox.name / "runtime.py"
    assert runtime_path.is_file()
    runtime = runtime_path.read_text()
    webapp = (rendered_sandbox / "src" / rendered_sandbox.name / "webapp.py").read_text()

    assert f"from {rendered_sandbox.name}.runtime import backend" in agent
    assert "create_sandbox_backend" not in agent
    assert "atexit.register" not in agent
    assert "from deepagents.backends import LangSmithSandbox" not in agent
    assert "from langsmith.sandbox import SandboxClient" not in agent
    assert f"from {rendered_sandbox.name}.sandbox import create_sandbox_backend" in runtime
    assert "backend, cleanup_sandbox = create_sandbox_backend()" in runtime
    assert "atexit.register(cleanup_sandbox)" in runtime
    assert f"from {rendered_sandbox.name}.runtime import cleanup_sandbox" in webapp
    assert f"from {rendered_sandbox.name}.agent import cleanup_sandbox" not in webapp


def test_file_graph_and_package_webapp_share_one_runtime_owner(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = json.loads((rendered_sandbox / "langgraph.json").read_text())
    graph_path_text, _ = config["graphs"]["sandbox"].split(":", maxsplit=1)
    graph_path = rendered_sandbox / graph_path_text.removeprefix("./")
    assert graph_path.name == "agent.py"
    webapp_path_text, app_name = config["http"]["app"].split(":", maxsplit=1)
    webapp_path = Path(webapp_path_text.removeprefix("./"))
    assert webapp_path.name == "webapp.py"
    assert app_name == "app"

    package_name = rendered_sandbox.name
    factory_calls = 0
    provider_create_calls: list[object] = []
    remote = types.SimpleNamespace(id="sandbox-id")

    class FakeDaytona:
        def create(self):
            provider_create_calls.append(remote)
            return remote

        def delete(self, value):
            pass

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.syspath_prepend(str(rendered_sandbox / "src"))
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FakeBackend),
    )
    monkeypatch.setitem(
        sys.modules,
        "deepagents",
        types.SimpleNamespace(create_deep_agent=lambda **kwargs: types.SimpleNamespace(**kwargs)),
    )
    monkeypatch.setitem(sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
    fake_langchain = types.ModuleType("langchain")
    fake_langchain.__path__ = []
    monkeypatch.setitem(sys.modules, "langchain", fake_langchain)
    monkeypatch.setitem(
        sys.modules,
        "langchain.chat_models",
        types.SimpleNamespace(init_chat_model=lambda **kwargs: types.SimpleNamespace(**kwargs)),
    )

    class FakeFastAPI:
        def __init__(self, *, lifespan):
            self.lifespan = lifespan

    monkeypatch.setitem(sys.modules, "fastapi", types.SimpleNamespace(FastAPI=FakeFastAPI))

    sandbox_module = importlib.import_module(f"{package_name}.sandbox")
    create_sandbox_backend = sandbox_module.create_sandbox_backend

    def count_factory_calls(*args, **kwargs):
        nonlocal factory_calls
        factory_calls += 1
        return create_sandbox_backend(*args, **kwargs)

    monkeypatch.setattr(sandbox_module, "create_sandbox_backend", count_factory_calls)

    graph_spec = importlib.util.spec_from_file_location("langgraph_generated_graph", graph_path)
    assert graph_spec is not None and graph_spec.loader is not None
    graph_module = importlib.util.module_from_spec(graph_spec)
    monkeypatch.setitem(sys.modules, graph_spec.name, graph_module)
    graph_spec.loader.exec_module(graph_module)

    webapp_module_name = ".".join(webapp_path.with_suffix("").parts[1:])
    webapp_module = importlib.import_module(webapp_module_name)

    assert factory_calls == 1
    assert len(provider_create_calls) == 1
    runtime_module = sys.modules[f"{package_name}.runtime"]
    assert graph_module.backend is runtime_module.backend
    assert webapp_module.cleanup_sandbox is runtime_module.cleanup_sandbox
    runtime_module.cleanup_sandbox()


def test_daytona_backend_and_cleanup(rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[object] = []
    sandbox = object()

    class FakeDaytona:
        def create(self):
            events.append("create")
            return sandbox

        def delete(self, value):
            events.append(("delete", value))

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    backend, cleanup = module.create_sandbox_backend("daytona")
    assert backend.sandbox is sandbox
    cleanup()
    cleanup()
    assert events == ["create", ("delete", sandbox)]


def test_langsmith_backend_and_cleanup(rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[object] = []
    remote = types.SimpleNamespace(name="sandbox-id")

    class FakeClient:
        def create_sandbox(self):
            events.append("create")
            return remote

        def delete_sandbox(self, name):
            events.append(("delete", name))

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setitem(
        sys.modules,
        "langsmith.sandbox",
        types.SimpleNamespace(SandboxClient=FakeClient),
    )
    monkeypatch.setitem(
        sys.modules,
        "deepagents.backends",
        types.SimpleNamespace(LangSmithSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    backend, cleanup = module.create_sandbox_backend("langsmith")
    assert backend.sandbox is remote
    cleanup()
    cleanup()
    assert events == ["create", ("delete", "sandbox-id")]


def test_daytona_adapter_failure_cleans_up_and_reraises(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[object] = []
    sandbox = object()

    class AdapterError(RuntimeError):
        pass

    class FakeDaytona:
        def create(self):
            events.append("create")
            return sandbox

        def delete(self, value):
            events.append(("delete", value))

    class FailingBackend:
        def __init__(self, *, sandbox):
            events.append(("adapter", sandbox))
            raise AdapterError

    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FailingBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    with pytest.raises(AdapterError):
        module.create_sandbox_backend("daytona")
    assert events == ["create", ("adapter", sandbox), ("delete", sandbox)]


def test_langsmith_adapter_failure_cleans_up_and_reraises(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[object] = []
    remote = types.SimpleNamespace(name="sandbox-id")

    class AdapterError(RuntimeError):
        pass

    class FakeClient:
        def create_sandbox(self):
            events.append("create")
            return remote

        def delete_sandbox(self, name):
            events.append(("delete", name))

    class FailingBackend:
        def __init__(self, *, sandbox):
            events.append(("adapter", sandbox))
            raise AdapterError

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setitem(
        sys.modules,
        "langsmith.sandbox",
        types.SimpleNamespace(SandboxClient=FakeClient),
    )
    monkeypatch.setitem(
        sys.modules,
        "deepagents.backends",
        types.SimpleNamespace(LangSmithSandbox=FailingBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    with pytest.raises(AdapterError):
        module.create_sandbox_backend("langsmith")
    assert events == ["create", ("adapter", remote), ("delete", "sandbox-id")]


def test_no_provider_argument_defaults_to_daytona(rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sandbox = object()

    class FakeDaytona:
        def create(self):
            return sandbox

        def delete(self, value):
            pass

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.delenv("AGENTSEEK_SANDBOX_PROVIDER", raising=False)
    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    backend, cleanup = module.create_sandbox_backend()
    assert backend.sandbox is sandbox
    cleanup()


def test_provider_environment_selects_langsmith(rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    remote = types.SimpleNamespace(name="sandbox-id")

    class FakeClient:
        def create_sandbox(self):
            return remote

        def delete_sandbox(self, name):
            pass

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.setenv("AGENTSEEK_SANDBOX_PROVIDER", "langsmith")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setitem(
        sys.modules,
        "langsmith.sandbox",
        types.SimpleNamespace(SandboxClient=FakeClient),
    )
    monkeypatch.setitem(
        sys.modules,
        "deepagents.backends",
        types.SimpleNamespace(LangSmithSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    backend, cleanup = module.create_sandbox_backend()
    assert backend.sandbox is remote
    cleanup()


def test_unsupported_provider_environment_fails_before_provider_imports(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class BombModule(types.ModuleType):
        def __getattr__(self, name: str):
            raise AssertionError

    monkeypatch.setenv("AGENTSEEK_SANDBOX_PROVIDER", "other")
    monkeypatch.setitem(sys.modules, "daytona", BombModule("daytona"))
    monkeypatch.setitem(sys.modules, "langchain_daytona", BombModule("langchain_daytona"))
    monkeypatch.setitem(sys.modules, "deepagents.backends", BombModule("deepagents.backends"))
    monkeypatch.setitem(sys.modules, "langsmith.sandbox", BombModule("langsmith.sandbox"))
    module = _load_sandbox_module(rendered_sandbox)
    with pytest.raises(ValueError, match="AGENTSEEK_SANDBOX_PROVIDER='other'"):
        module.create_sandbox_backend()


@pytest.mark.parametrize(
    ("provider", "credential"),
    [
        ("daytona", "DAYTONA_API_KEY"),
        ("langsmith", "LANGSMITH_API_KEY"),
    ],
)
def test_provider_requires_credential(
    rendered_sandbox: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    credential: str,
) -> None:
    monkeypatch.delenv(credential, raising=False)
    module = _load_sandbox_module(rendered_sandbox)
    with pytest.raises(
        RuntimeError,
        match=rf"{credential} is required when AGENTSEEK_SANDBOX_PROVIDER={provider}",
    ):
        module.create_sandbox_backend(provider)


def test_cleanup_suppresses_provider_delete_errors_and_emits_safe_warning(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sandbox = types.SimpleNamespace(id="sandbox-123")
    delete_calls = 0

    class DeleteError(RuntimeError):
        def __init__(self) -> None:
            super().__init__("credential=do-not-leak arbitrary provider detail")

    class FakeDaytona:
        def create(self):
            return sandbox

        def delete(self, value):
            nonlocal delete_calls
            delete_calls += 1
            raise DeleteError

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    _, cleanup = module.create_sandbox_backend("daytona")
    with pytest.warns(RuntimeWarning) as captured:
        cleanup()
    cleanup()

    assert delete_calls == 1
    warning = str(captured[0].message)
    assert "daytona" in warning
    assert "sandbox-123" in warning
    assert "delete it manually" in warning.lower()
    assert "provider dashboard" in warning.lower()
    assert "do-not-leak" not in warning
    assert "credential" not in warning

    _, strict_cleanup = module.create_sandbox_backend("daytona")
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        strict_cleanup()
    assert delete_calls == 2


def test_cleanup_is_idempotent_when_two_threads_call_concurrently(
    rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sandbox = types.SimpleNamespace(id="sandbox-123")
    delete_calls = 0
    delete_count_lock = threading.Lock()
    callers_ready = threading.Barrier(3)
    callers_entered = threading.Condition()
    caller_count = 0
    delete_started = threading.Event()
    release_delete = threading.Event()

    class FakeDaytona:
        def create(self):
            return sandbox

        def delete(self, value):
            nonlocal delete_calls
            with delete_count_lock:
                delete_calls += 1
            delete_started.set()
            assert release_delete.wait(timeout=5)

    class FakeBackend:
        def __init__(self, *, sandbox):
            self.sandbox = sandbox

    monkeypatch.setenv("DAYTONA_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "daytona", types.SimpleNamespace(Daytona=FakeDaytona))
    monkeypatch.setitem(
        sys.modules,
        "langchain_daytona",
        types.SimpleNamespace(DaytonaSandbox=FakeBackend),
    )
    module = _load_sandbox_module(rendered_sandbox)
    _, cleanup = module.create_sandbox_backend("daytona")

    def call_cleanup() -> None:
        nonlocal caller_count
        callers_ready.wait(timeout=5)
        with callers_entered:
            caller_count += 1
            callers_entered.notify_all()
        cleanup()

    threads = [threading.Thread(target=call_cleanup) for _ in range(2)]
    for thread in threads:
        thread.start()
    try:
        callers_ready.wait(timeout=5)
        with callers_entered:
            assert callers_entered.wait_for(lambda: caller_count == 2, timeout=5)
        assert delete_started.wait(timeout=5)
    finally:
        release_delete.set()
        for thread in threads:
            thread.join(timeout=5)
            assert not thread.is_alive()

    assert delete_calls == 1
