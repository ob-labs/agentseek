"""Tests for ``agentseek create``: template discovery, listing, and generation."""

from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest
from agentseek_cli.app import build_app
from agentseek_cli.commands import create as create_module
from agentseek_cli.commands.create import TemplateSource
from typer.testing import CliRunner


def _runner() -> CliRunner:
    return CliRunner()


# -- spec validation / error paths -----------------------------------------


def test_unknown_type_exits_2() -> None:
    result = _runner().invoke(build_app(), ["create", "not-a-real-type"])
    assert result.exit_code == 2
    assert "Unknown framework type" in result.output


def test_list_templates_for_type_prints_bundled_names() -> None:
    result = _runner().invoke(build_app(), ["create", "langchain", "--list-templates"])
    assert result.exit_code == 0
    assert "Available langchain templates" in result.output
    assert "default" in result.output
    assert "cli-remote" in result.output


def test_list_templates_without_type_lists_all_known_types() -> None:
    result = _runner().invoke(build_app(), ["create", "--list-templates"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert f"Available {project_type} templates" in result.output


# -- template resolution ---------------------------------------------------


def test_resolve_type_template_local() -> None:
    """Local repo should resolve to an on-disk path with cookiecutter.json."""
    source = create_module._resolve_type_template("bub", "default")
    # When running from the repo, template should be a local path.
    template_path = Path(source.template)
    assert template_path.is_dir()
    assert (template_path / "cookiecutter.json").is_file()
    assert source.directory is None  # local path — no directory needed


def test_resolve_type_template_remote_fallback(monkeypatch) -> None:
    """When there's no local repo, should fall back to remote URL."""
    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    source = create_module._resolve_type_template("deepagents", "default")
    assert source.template == create_module.REPO_URL
    assert source.directory == "templates/deepagents/default"


def test_list_templates_returns_names() -> None:
    templates = create_module._list_templates("langchain")
    assert "default" in templates
    assert "cli-remote" in templates


def test_list_templates_unknown_type_returns_empty() -> None:
    assert create_module._list_templates("totally-not-a-type") == []


# -- type/name spec parsing ------------------------------------------------


def test_spec_with_slash_splits_into_type_and_name() -> None:
    """``langchain/cli-remote`` → type=langchain, name=cli-remote."""
    args = create_module._parse_argv(["langchain/cli-remote", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "langchain"
    assert template_name == "cli-remote"


def test_spec_plain_type_returns_none_name() -> None:
    args = create_module._parse_argv(["deepagents", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "deepagents"
    assert template_name is None


def test_spec_none_returns_none_none() -> None:
    args = create_module._parse_argv(["--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type is None
    assert template_name is None


# -- external spec detection -----------------------------------------------


def test_is_external_spec_url() -> None:
    assert create_module._is_external_spec("https://github.com/x/y.git")
    assert create_module._is_external_spec("git@github.com:x/y.git")
    assert create_module._is_external_spec("/opt/my-template")


def test_is_external_spec_local_type() -> None:
    assert not create_module._is_external_spec("deepagents")
    assert not create_module._is_external_spec("langchain/cli-remote")


# -- integration with cookiecutter via monkeypatch -------------------------


def test_create_with_explicit_template_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        # Simulate cookiecutter generating a project.
        target = output_dir / "fake-project"
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("ok", encoding="utf-8")

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_app(),
        ["create", "deepagents", "--template", "default", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    # May resolve locally (path with deepagents/default) or remotely (URL + directory).
    if source.directory is not None:
        # Remote fallback: directory carries the subpath.
        assert "deepagents/default" in source.directory
    else:
        # Local: template path ends with deepagents/default.
        assert "deepagents" in source.template and "default" in source.template
    assert captured["no_input"] is True
    assert Path(str(captured["output_dir"])) == tmp_path
    assert (tmp_path / "fake-project" / "README.md").read_text(encoding="utf-8") == "ok"


def test_create_with_slash_spec_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    """``agentseek create langchain/cli-remote --no-input`` should resolve correctly."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_app(),
        ["create", "langchain/cli-remote", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    # May resolve locally or remotely.
    if source.directory is not None:
        assert "langchain/cli-remote" in source.directory
    else:
        assert "langchain" in source.template and "cli-remote" in source.template


def test_create_with_url_spec_passes_through(monkeypatch, tmp_path: Path) -> None:
    """External URL spec should be passed directly to cookiecutter."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_app(),
        ["create", "https://github.com/foo/bar.git", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == "https://github.com/foo/bar.git"


# -- real cookiecutter end-to-end ------------------------------------------


def test_create_real_cookiecutter_generates_files(tmp_path: Path) -> None:
    """End-to-end: actually run cookiecutter on a local template."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "default"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)
    assert generated.is_dir()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / "src").is_dir()
    assert generated.name == "my_deepagent"
    settings_py = generated / "src" / "my_deepagent" / "settings.py"
    assert settings_py.is_file()
    content = settings_py.read_text(encoding="utf-8")
    assert "AGENTSEEK_MODEL" in content


def test_deepagents_research_template_metadata_and_docs_exist() -> None:
    """The pure DeepAgents research template should be listed and documented."""
    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"

    template_path = local_root / "deepagents" / "research"
    assert (template_path / "cookiecutter.json").is_file()
    assert (template_path / "README.md").is_file()
    cookiecutter_data = json.loads((template_path / "cookiecutter.json").read_text(encoding="utf-8"))
    assert cookiecutter_data["default_model"] == "openai:Pro/zai-org/GLM-5.1"

    templates_index = local_root / "index.json"
    data = json.loads(templates_index.read_text(encoding="utf-8"))
    assert "deepagents/research" in data


def test_deepagents_research_template_renders_docs_and_streaming_frontend(
    tmp_path: Path,
) -> None:
    """The rendered project should include docs and the streaming frontend shell."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "research"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)

    readme = generated / "README.md"
    frontend = generated / "frontend"
    frontend_package = frontend / "package.json"
    frontend_env = frontend / ".env.example"
    frontend_app = frontend / "src" / "App.tsx"
    frontend_tool_card = frontend / "src" / "ToolCallCard.tsx"
    frontend_app_test = frontend / "src" / "App.test.tsx"
    frontend_tool_card_test = frontend / "src" / "ToolCallCard.test.tsx"
    agent_py = generated / "src" / "research_deepagent" / "agent.py"
    env_example = generated / ".env.example"

    assert readme.is_file()
    readme_text = readme.read_text(encoding="utf-8")
    assert "## Setup" in readme_text
    assert "## Run" in readme_text
    assert "## Smoke test" in readme_text
    assert "langgraph dev" in readme_text
    assert "npm install --prefix frontend" in readme_text

    assert frontend_package.is_file()
    assert frontend_env.is_file()
    assert frontend_app.is_file()
    assert frontend_tool_card.is_file()
    assert frontend_app_test.is_file()
    assert frontend_tool_card_test.is_file()
    assert '"test": "vitest run --environment jsdom"' in frontend_package.read_text(encoding="utf-8")
    assert agent_py.is_file()
    agent_text = agent_py.read_text(encoding="utf-8")
    assert "stream_chunk_timeout=STREAM_CHUNK_TIMEOUT_S" in agent_text
    assert "LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S" in agent_text
    assert env_example.is_file()
    assert "LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S=300" in env_example.read_text(encoding="utf-8")


def test_deepagents_research_fetch_helper_follows_redirects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The rendered research helper should follow redirects when fetching pages."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "research"

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)
    monkeypatch.syspath_prepend(str(generated / "src"))
    sys.modules.pop("research_deepagent.tools", None)

    markdownify_module = types.ModuleType("markdownify")
    cast(Any, markdownify_module).markdownify = lambda text: text
    monkeypatch.setitem(sys.modules, "markdownify", markdownify_module)

    tavily_module = types.ModuleType("tavily")

    class FakeTavilyClient:
        def search(self, *_args: object, **_kwargs: object) -> dict[str, list[dict[str, str]]]:
            return {"results": []}

    cast(Any, tavily_module).TavilyClient = FakeTavilyClient
    monkeypatch.setitem(sys.modules, "tavily", tavily_module)

    langchain_core_module = types.ModuleType("langchain_core")
    langchain_core_tools_module = types.ModuleType("langchain_core.tools")
    cast(Any, langchain_core_tools_module).InjectedToolArg = object
    cast(Any, langchain_core_tools_module).tool = lambda **_kwargs: lambda fn: fn
    monkeypatch.setitem(sys.modules, "langchain_core", langchain_core_module)
    monkeypatch.setitem(sys.modules, "langchain_core.tools", langchain_core_tools_module)

    module = importlib.import_module("research_deepagent.tools")
    captured: dict[str, object] = {}

    class FakeResponse:
        text = "<h1>Redirected</h1>"

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(module.httpx, "get", fake_get)

    result = module.fetch_webpage_content("https://example.com/redirect")

    assert "Redirected" in result
    assert captured["follow_redirects"] is True


def test_deepagents_research_agent_invalid_timeout_env_uses_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid stream timeout env should not crash generated agent startup."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "research"

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)
    generated_src = str(generated / "src")
    monkeypatch.syspath_prepend(generated_src)
    sys.modules.pop("research_deepagent.agent", None)
    sys.modules.pop("research_deepagent.tools", None)

    dotenv_module = types.ModuleType("dotenv")
    cast(Any, dotenv_module).load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, "dotenv", dotenv_module)

    deepagents_module = types.ModuleType("deepagents")
    cast(Any, deepagents_module).create_deep_agent = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "deepagents", deepagents_module)

    init_calls: list[dict[str, object]] = []

    def fake_init_chat_model(model: str, **kwargs: object) -> dict[str, object]:
        init_calls.append({"model": model, **kwargs})
        return {"model": model, **kwargs}

    langchain_module = types.ModuleType("langchain")
    langchain_chat_models_module = types.ModuleType("langchain.chat_models")
    cast(Any, langchain_chat_models_module).init_chat_model = fake_init_chat_model
    monkeypatch.setitem(sys.modules, "langchain", langchain_module)
    monkeypatch.setitem(sys.modules, "langchain.chat_models", langchain_chat_models_module)

    fake_tools_module = types.ModuleType("research_deepagent.tools")
    cast(Any, fake_tools_module).tavily_search = object()
    cast(Any, fake_tools_module).think_tool = object()
    monkeypatch.setitem(sys.modules, "research_deepagent.tools", fake_tools_module)

    monkeypatch.setenv("LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S", "not-a-number")

    module = importlib.import_module("research_deepagent.agent")

    assert module.STREAM_CHUNK_TIMEOUT_S == 300.0
    assert init_calls[0]["stream_chunk_timeout"] == 300.0


@pytest.mark.parametrize(
    ("project_type", "template_name"),
    [
        ("bub", "default"),
        ("langchain", "default"),
    ],
)
def test_ag_ui_templates_generate_frontend_and_serve_script(
    tmp_path: Path,
    project_type: str,
    template_name: str,
) -> None:
    """AG-UI templates should ship a runnable frontend and a `serve` entry point."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / project_type / template_name
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)

    pyproject = generated / "pyproject.toml"
    frontend = generated / "frontend"
    frontend_package = frontend / "package.json"
    frontend_app = frontend / "src" / "App.tsx"
    frontend_main = frontend / "src" / "main.tsx"
    env_example = generated / ".env.example"

    assert pyproject.is_file()
    assert 'serve = "my_' in pyproject.read_text(encoding="utf-8")
    assert frontend_package.is_file()
    assert frontend_app.is_file()
    assert frontend_main.is_file()
    assert "FRONTEND_PORT" in env_example.read_text(encoding="utf-8")
