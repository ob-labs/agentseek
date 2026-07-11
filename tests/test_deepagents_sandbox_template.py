from __future__ import annotations

import ast
import importlib.util
import sys
import tomllib
import types
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


def test_rendered_dependencies_include_both_sandbox_integrations(rendered_sandbox: Path) -> None:
    project = tomllib.loads((rendered_sandbox / "pyproject.toml").read_text())
    dependencies = project["project"]["dependencies"]
    assert "langchain-daytona>=0.0.7" in dependencies
    assert "langsmith[sandbox]" in dependencies


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


def test_provider_normalization(rendered_sandbox: Path) -> None:
    module = _load_sandbox_module(rendered_sandbox)
    assert module.normalize_sandbox_provider("DAYTONA") == "daytona"
    assert module.normalize_sandbox_provider(" langsmith ") == "langsmith"
    with pytest.raises(ValueError, match="daytona, langsmith"):
        module.normalize_sandbox_provider("other")


def test_rendered_agent_uses_provider_factory(rendered_sandbox: Path) -> None:
    agent = (rendered_sandbox / "src" / rendered_sandbox.name / "agent.py").read_text()
    assert f"from {rendered_sandbox.name}.sandbox import create_sandbox_backend" in agent
    assert "backend, _cleanup_sandbox = create_sandbox_backend()" in agent
    assert "atexit.register(_cleanup_sandbox)" in agent
    assert "from deepagents.backends import LangSmithSandbox" not in agent
    assert "from langsmith.sandbox import SandboxClient" not in agent


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


def test_cleanup_suppresses_provider_delete_errors(rendered_sandbox: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sandbox = object()

    class FakeDaytona:
        def create(self):
            return sandbox

        def delete(self, value):
            raise RuntimeError

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
    cleanup()
