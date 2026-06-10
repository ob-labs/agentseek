"""Tests for ``agentseek new``: template discovery, listing, and generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentseek.cli.commands import new as create_module
from agentseek.cli.commands.new import TemplateSource
from tests.cli_commands.helpers import build_command_app


def _runner() -> CliRunner:
    return CliRunner()


def _mock_remote_template_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    index: dict[str, str],
    *,
    cached: bool = False,
) -> list[tuple[str, str | None, str, bool]]:
    cookiecutters_dir = tmp_path / "cookiecutters"
    repo_root = cookiecutters_dir / "agentseek" if cached else tmp_path / "downloaded-agentseek"
    templates_root = repo_root / "templates"
    templates_root.mkdir(parents=True)
    (templates_root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    for template in index:
        template_dir = templates_root / template
        template_dir.mkdir(parents=True)
        (template_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")
    clone_calls: list[tuple[str, str | None, str, bool]] = []

    def fake_get_user_config() -> dict[str, str]:
        return {"cookiecutters_dir": str(cookiecutters_dir)}

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append((repo_url, checkout, str(clone_to_dir), no_input))
        return str(repo_root)

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    monkeypatch.setattr("cookiecutter.config.get_user_config", fake_get_user_config)
    monkeypatch.setattr("cookiecutter.vcs.clone", fake_clone)
    return clone_calls


# -- spec validation / error paths -----------------------------------------


def test_help_exits_0() -> None:
    result = _runner().invoke(build_command_app(), ["new", "--help"])
    assert result.exit_code == 0
    assert "agentseek new" in result.output


def test_unknown_type_exits_2() -> None:
    result = _runner().invoke(build_command_app(), ["new", "not-a-real-type"])
    assert result.exit_code == 2
    assert "Unknown framework type" in result.output


def test_list_templates_for_type_prints_bundled_names() -> None:
    result = _runner().invoke(build_command_app(), ["new", "langchain", "--list-templates"])
    assert result.exit_code == 0
    assert "langchain" in result.output
    assert "default" in result.output
    assert "cli-remote" in result.output
    assert "markdown-messages" in result.output


def test_list_templates_without_type_lists_all_known_types() -> None:
    result = _runner().invoke(build_command_app(), ["new", "--list-templates"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert project_type in result.output


def test_template_flag_no_value_lists_all_templates() -> None:
    """``agentseek new --template`` (no value) should list all templates."""
    result = _runner().invoke(build_command_app(), ["new", "--template"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert project_type in result.output
    assert "Usage:" in result.output


def test_template_flag_no_value_with_type_lists_type_templates() -> None:
    """``agentseek new langchain --template`` should list langchain templates only."""
    result = _runner().invoke(build_command_app(), ["new", "langchain", "--template"])
    assert result.exit_code == 0
    assert "langchain" in result.output
    assert "cli-remote" in result.output
    assert "Usage:" not in result.output


def test_template_flag_no_value_lists_remote_templates_without_checkout(monkeypatch, tmp_path: Path) -> None:
    """Installed CLI should download templates before listing them."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {
            "deepagents/default": "Default DeepAgents template.",
            "langchain/remote-only": "Remote-only LangChain template.",
            "bub/default": "Default Bub template.",
        },
    )

    result = _runner().invoke(build_command_app(), ["new", "--template"])

    assert result.exit_code == 0, result.output
    assert clone_calls == [(create_module.REPO_URL, None, str(tmp_path / "cookiecutters"), True)]
    assert "deepagents/default" in result.output
    assert "langchain/remote-only" in result.output
    assert "Remote-only LangChain template." in result.output
    assert "Usage:" in result.output


def test_template_flag_no_value_for_type_uses_remote_checkout(monkeypatch, tmp_path: Path) -> None:
    """``--checkout`` should be forwarded to cookiecutter's clone path."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {"langchain/remote-only": "Remote-only LangChain template."},
    )

    result = _runner().invoke(build_command_app(), ["new", "langchain", "--template", "--checkout", "release/next"])

    assert result.exit_code == 0, result.output
    assert clone_calls == [(create_module.REPO_URL, "release/next", str(tmp_path / "cookiecutters"), True)]
    assert "langchain/remote-only" in result.output
    assert "Usage:" not in result.output


def test_template_flag_no_value_reuses_cached_remote_repo(monkeypatch, tmp_path: Path) -> None:
    """Installed CLI should use the cookiecutter cache before cloning."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {"langchain/cached": "Cached LangChain template."},
        cached=True,
    )

    result = _runner().invoke(build_command_app(), ["new", "langchain", "--template"])

    assert result.exit_code == 0, result.output
    assert clone_calls == []
    assert "langchain/cached" in result.output
    assert "Cached LangChain template." in result.output


# -- template resolution ---------------------------------------------------


def test_resolve_type_template_local() -> None:
    """Local repo should resolve to an on-disk path with cookiecutter.json."""
    local_root = create_module._local_templates_root()
    assert local_root is not None
    source = create_module._resolve_type_template("bub", "default", templates_root=local_root)
    # When running from the repo, template should be a local path.
    template_path = Path(source.template)
    assert template_path.is_dir()
    assert (template_path / "cookiecutter.json").is_file()
    assert source.directory is None  # local path — no directory needed


def test_list_templates_returns_names() -> None:
    templates = create_module._list_templates("langchain")
    assert "default" in templates
    assert "cli-remote" in templates
    assert "markdown-messages" in templates


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
        build_command_app(),
        ["new", "deepagents", "--template", "default", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.directory is None
    assert "deepagents" in source.template and "default" in source.template
    assert captured["no_input"] is True
    assert Path(str(captured["output_dir"])) == tmp_path
    assert (tmp_path / "fake-project" / "README.md").read_text(encoding="utf-8") == "ok"


def test_create_with_slash_spec_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    """``agentseek new langchain/cli-remote --no-input`` should resolve correctly."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["new", "langchain/cli-remote", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.directory is None
    assert "langchain" in source.template and "cli-remote" in source.template


def test_create_with_url_spec_passes_through(monkeypatch, tmp_path: Path) -> None:
    """External URL spec should be passed directly to cookiecutter."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["new", "https://github.com/foo/bar.git", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == "https://github.com/foo/bar.git"


# -- real cookiecutter end-to-end ------------------------------------------


def _patch_template_for_test(template_path: Path, tmp_path: Path) -> Path:
    """Copy a template dir and inject ``_agentseek_source_path`` into its
    ``cookiecutter.json`` so it can render without the CLI runtime context."""
    import shutil

    patched = tmp_path / "patched_template" / template_path.name
    shutil.copytree(template_path, patched)
    cc_file = patched / "cookiecutter.json"
    cc_data = json.loads(cc_file.read_text(encoding="utf-8"))
    if "_agentseek_source_path" not in cc_data:
        cc_data["_agentseek_source_path"] = ""
    cc_file.write_text(json.dumps(cc_data, indent=2) + "\n", encoding="utf-8")
    return patched


def test_create_real_cookiecutter_generates_files(tmp_path: Path) -> None:
    """End-to-end: actually run cookiecutter on a local template."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = _patch_template_for_test(local_root / "deepagents" / "default", tmp_path)
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(
        str(template_path),
        output_dir=str(tmp_path),
        no_input=True,
    )
    generated = Path(output)
    assert generated.is_dir()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / "src").is_dir()
    assert generated.name == "my_deepagent"
    settings_py = generated / "src" / "my_deepagent" / "settings.py"
    assert settings_py.is_file()
    content = settings_py.read_text(encoding="utf-8")
    assert "AGENTSEEK_MODEL" in content


def test_markdown_messages_template_metadata_and_docs_exist() -> None:
    """The pure markdown-messages template should be listed and documented."""
    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"

    template_path = local_root / "langchain" / "markdown-messages"
    assert (template_path / "cookiecutter.json").is_file()
    assert (template_path / "README.md").is_file()
    cookiecutter_data = json.loads((template_path / "cookiecutter.json").read_text(encoding="utf-8"))
    assert "default_model" in cookiecutter_data

    templates_index = local_root / "index.json"
    data = json.loads(templates_index.read_text(encoding="utf-8"))
    assert "langchain/markdown-messages" in data


def test_markdown_messages_template_renders_backend_and_frontend(tmp_path: Path) -> None:
    """Rendered markdown-messages project should include the stream-ready files."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "langchain" / "markdown-messages"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)

    assert (generated / "README.md").is_file()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / ".env.example").is_file()
    assert (generated / "langgraph.json").is_file()
    assert (generated / "frontend" / "package.json").is_file()
    assert (generated / "frontend" / "src" / "App.tsx").is_file()
    assert (generated / "src" / "markdown_messages_agent" / "agent.py").is_file()


def test_deepagents_research_template_metadata_and_docs_exist() -> None:
    """The pure DeepAgents research template should be listed and documented."""
    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"

    template_path = local_root / "deepagents" / "research"
    assert (template_path / "cookiecutter.json").is_file()
    assert (template_path / "README.md").is_file()
    cookiecutter_data = json.loads((template_path / "cookiecutter.json").read_text(encoding="utf-8"))
    assert cookiecutter_data["default_model_provider"] == "openai"
    assert cookiecutter_data["default_model"] == "gpt-4.1-mini"

    templates_index = local_root / "index.json"
    data = json.loads(templates_index.read_text(encoding="utf-8"))
    assert "deepagents/research" in data


def test_deepagents_research_template_renders_docs_and_streaming_frontend(
    tmp_path: Path,
) -> None:
    """The rendered project should include docs, backend, and the streaming frontend."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "research"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)

    assert (generated / "README.md").is_file()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / ".env.example").is_file()

    agent_py = generated / "src" / "research_deepagent" / "agent.py"
    tools_py = generated / "src" / "research_deepagent" / "tools.py"
    prompts_py = generated / "src" / "research_deepagent" / "prompts.py"
    assert agent_py.is_file()
    assert tools_py.is_file()
    assert prompts_py.is_file()

    frontend = generated / "frontend"
    assert (frontend / "package.json").is_file()
    assert (frontend / "src" / "App.tsx").is_file()
    assert (frontend / "src" / "TodoList.tsx").is_file()
    assert (frontend / "src" / "ToolCallCard.tsx").is_file()

    agent_text = agent_py.read_text(encoding="utf-8")
    assert "SUPPORTED_MODEL_PROVIDERS" in agent_text
    assert "_normalize_provider" in agent_text
    assert "follow_redirects=True" in tools_py.read_text(encoding="utf-8")


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

    assert (generated / "pyproject.toml").is_file()
    assert (generated / "README.md").is_file()
    assert (generated / ".env.example").is_file()
    assert (generated / "frontend" / "package.json").is_file()
    assert (generated / "frontend" / "src" / "App.tsx").is_file()
    assert (generated / "frontend" / "src" / "main.tsx").is_file()

    pyproject_text = (generated / "pyproject.toml").read_text(encoding="utf-8")
    assert 'serve = "my_' in pyproject_text
    assert '"agentseek"' in pyproject_text


def test_langchain_default_template_includes_feishu_use_case(tmp_path: Path) -> None:
    """The langchain/default template should ship a first-class Feishu path."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "langchain" / "default"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)

    pyproject_text = (generated / "pyproject.toml").read_text(encoding="utf-8")
    assert '"bub-feishu"' in pyproject_text
    assert 'serve-feishu = "my_' in pyproject_text
