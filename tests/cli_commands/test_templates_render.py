"""Render-check regression test for every cookiecutter template under ``templates/``.

For each template, render it with ``no_input=True`` (using ``cookiecutter.json``
defaults) into a temporary directory and assert the generated tree carries the
invariants every template must satisfy.

This test does *not* install dependencies, run ``uv sync``, or boot the
generated project — that lives in a later smoke script. The point here is to
catch Jinja errors, missing files, and unsubstituted variables before they hit
``main``.
"""

from __future__ import annotations

import json
import shutil
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from cookiecutter.main import cookiecutter
from typer.testing import CliRunner

from agentseek.cli.commands import create as create_module
from tests.cli_commands.helpers import build_command_app


def _patch_template_for_test(template_dir: Path, tmp_path: Path) -> Path:
    """Copy a template dir for isolated cookiecutter rendering."""
    patched = tmp_path / "patched_template" / template_dir.name
    shutil.copytree(template_dir, patched)
    return patched


def _discover_templates() -> list[tuple[str, str, Path]]:
    """Walk ``templates/`` and yield ``(type, name, template_dir)`` for each
    directory that contains a ``cookiecutter.json``.

    Returns an empty list when the templates root cannot be found (e.g. when
    the package is installed without a checkout). The test that consumes this
    asserts non-empty to fail loudly in that case.
    """
    root = create_module._local_templates_root()
    if root is None:
        return []
    discovered: list[tuple[str, str, Path]] = []
    for type_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for template_dir in sorted(p for p in type_dir.iterdir() if p.is_dir()):
            if (template_dir / "cookiecutter.json").is_file():
                discovered.append((type_dir.name, template_dir.name, template_dir))
    return discovered


TEMPLATES = _discover_templates()
seekdb_skill_templates = {
    ("bub", "contextseek"),
    ("langchain", "agentic-rag-hybrid"),
    ("langchain", "agentic-rag"),
    ("langchain", "agentic-rag-openvino"),
    ("langchain", "default"),
}
seekdb_skill_command = ["npx", "skills", "add", "oceanbase/seekdb-ecology-plugins", "--all"]
rag_host_binding_templates = {
    ("langchain", "agentic-rag-hybrid"),
    ("langchain", "agentic-rag"),
    ("langchain", "agentic-rag-openvino"),
}
language_instruction_templates = {
    ("deepagents", "research"),
    ("deepagents", "sandbox"),
    ("langchain", "agentic-rag"),
    ("langchain", "agentic-rag-hybrid"),
    ("langchain", "agentic-rag-openvino"),
    ("langchain", "cli-remote"),
    ("langchain", "default"),
    ("langchain", "markdown-messages"),
}
dependency_sync_templates = {
    ("deepagents", "content-builder"),
    ("deepagents", "research"),
    ("deepagents", "sandbox"),
    ("langchain", "agentic-rag-hybrid"),
}


def _assert_rag_template_host_binding(generated: Path, *, check_frontend_env: bool = False) -> None:
    """RAG frontend/backend dev servers bind locally by default and opt into remote hosts."""
    lifecycle_text = (generated / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8")
    vite_text = (generated / "frontend" / "vite.config.ts").read_text(encoding="utf-8")
    app_text = (generated / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    assert "[env.LANGGRAPH_HOST]" in lifecycle_text
    assert "--host ${LANGGRAPH_HOST:-127.0.0.1}" in lifecycle_text
    assert "FRONTEND_HOST" in vite_text
    assert "window.location.hostname" in app_text
    assert "agentseek task sync" in readme_text
    assert "agentseek task frontend" in readme_text
    assert "LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev" in readme_text
    if check_frontend_env:
        frontend_env_text = (generated / "frontend" / ".env.example").read_text(encoding="utf-8")
        assert "VITE_LANGGRAPH_API_URL=http://127.0.0.1" not in frontend_env_text


def _assert_bub_default_dependencies(dependencies: list[Any], pyproject_data: dict[str, Any]) -> None:
    assert "bub==0.3.9" in dependencies
    assert "agentseek-ag-ui" in dependencies
    assert "duty>=1.9" not in pyproject_data.get("dependency-groups", {}).get("dev", [])


def _assert_seekdb_skill_task(generated: Path, lifecycle_data: dict[str, Any]) -> None:
    task = lifecycle_data["tasks"]["seekdb-skills"]
    assert task["description"] == "Install recommended OceanBase seekdb agent skills."
    assert task["command"] == seekdb_skill_command
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    assert "agentseek task seekdb-skills" in readme_text
    assert "## Agent Skills" in readme_text


def _assert_langchain_default_template(generated: Path) -> None:
    env_text = (generated / ".env.example").read_text(encoding="utf-8")
    compose_text = (generated / "docker-compose.yml").read_text(encoding="utf-8")
    dev_text = (generated / "src" / generated.name / "dev.py").read_text(encoding="utf-8")
    assert "AGENTSEEK_PHOENIX_IMAGE=ghcr.io/agentseek-ai/agentseek-phoenix:main" in env_text
    assert "OCEANBASE_SEEKDB_IMAGE=quay.io/oceanbase/seekdb:latest" in env_text
    assert "${AGENTSEEK_PHOENIX_IMAGE:-ghcr.io/agentseek-ai/agentseek-phoenix:main}" in compose_text
    assert "${OCEANBASE_SEEKDB_IMAGE:-quay.io/oceanbase/seekdb:latest}" in compose_text
    assert "agentseek task frontend" in dev_text
    assert "npm install --prefix frontend" not in dev_text


def _assert_deepagents_content_builder_template(generated: Path) -> None:
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    agents_text = (generated / "AGENTS.md").read_text(encoding="utf-8")
    assert "agentseek task frontend" in readme_text
    assert "same language as the user's question" in agents_text


def _assert_deepagents_default_template(generated: Path) -> None:
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    binding_text = (generated / "src" / generated.name / "demo_binding.py").read_text(encoding="utf-8")
    assert "does not include a frontend" in readme_text
    assert "Answer in the same language as the user's question." in readme_text
    assert "Answer in the same language as the user's question." in binding_text


def _assert_language_instruction_template(generated: Path) -> None:
    agent_files = sorted((generated / "src" / generated.name).glob("*.py"))
    rendered_python = "\n".join(path.read_text(encoding="utf-8") for path in agent_files)
    assert "Answer in the same language as the user's question." in rendered_python


def _assert_agentic_rag_openvino_template(generated: Path) -> None:
    agent_text = (generated / "src" / generated.name / "agent.py").read_text(encoding="utf-8")
    converter_text = (generated / "src" / generated.name / "convert_models.py").read_text(encoding="utf-8")
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    assert '"optimum-cli", "export", "openvino"' in converter_text
    assert "python -m optimum.exporters.openvino" not in converter_text
    assert "from langgraph.graph import MessagesState, StateGraph" in agent_text
    assert "create_agent" not in agent_text
    assert "ChatHuggingFace" not in agent_text
    assert "Answer in the same language as the user's question." in agent_text
    assert "bind_tools" not in readme_text
    assert "deterministic retrieve-then-generate graph" in readme_text
    assert "agentseek task sync" in readme_text
    assert "uv sync" not in readme_text


def _assert_agentic_rag_hybrid_template(generated: Path, lifecycle_data: dict[str, Any]) -> None:
    env_text = (generated / ".env.example").read_text(encoding="utf-8")
    compose_text = (generated / "docker-compose.yml").read_text(encoding="utf-8")
    lifecycle_text = (generated / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8")
    pyproject_text = (generated / "pyproject.toml").read_text(encoding="utf-8")
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    app_text = (generated / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "AGENTSEEK_OTEL_ENABLED=false" in env_text
    assert "AGENTSEEK_API_KEY=" in env_text
    assert "AGENTSEEK_API_BASE=https://api.siliconflow.cn/v1" in env_text
    assert "OPENAI_API_BASE=" not in env_text
    assert "VITE_LANGGRAPH_API_URL=http://127.0.0.1" not in env_text
    assert "VITE_CUSTOM_ROUTES_URL=http://127.0.0.1" not in env_text
    assert "AGENTSEEK_PHOENIX_IMAGE=ghcr.io/agentseek-ai/agentseek-phoenix:main" in env_text
    assert "OCEANBASE_SEEKDB_IMAGE=quay.io/oceanbase/seekdb:latest" in env_text
    assert "${AGENTSEEK_PHOENIX_IMAGE:-ghcr.io/agentseek-ai/agentseek-phoenix:main}" in compose_text
    assert "${OCEANBASE_SEEKDB_IMAGE:-quay.io/oceanbase/seekdb:latest}" in compose_text
    assert "PHOENIX_SQL_DATABASE_URL: mysql://root@seekdb:2881/phoenix" in compose_text
    assert "AGENTSEEK_API_KEY" in lifecycle_data["env"]
    assert "AGENTSEEK_API_BASE" in lifecycle_data["env"]
    assert "agentseek task phoenix" in readme_text
    assert "agentseek doctor" in readme_text
    assert "LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev" in readme_text
    assert "custom/observability" in readme_text
    assert "window.location.hostname" in app_text
    assert "phoenix" in lifecycle_data["tasks"]
    assert "phoenix-stop" in lifecycle_data["tasks"]
    assert "mysql://127.0.0.1:2884/phoenix" in lifecycle_text
    assert "openinference-instrumentation-langchain" in pyproject_text


def _assert_frontend_package_json(generated: Path) -> None:
    """Validate package.json when the rendered template includes a frontend."""
    frontend_package = generated / "frontend" / "package.json"
    if not frontend_package.is_file():
        return

    try:
        json.loads(frontend_package.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"frontend/package.json is not valid JSON: {exc}")


def _assert_dependency_sync_task(
    type_name: str,
    template_name: str,
    generated: Path,
    lifecycle_data: dict[str, Any],
) -> None:
    if (type_name, template_name) not in dependency_sync_templates:
        return

    assert "sync" in lifecycle_data["tasks"]
    assert lifecycle_data["tasks"]["sync"]["command"] == ["uv", "sync"]
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    assert "agentseek task sync" in readme_text


def test_at_least_one_template_discovered() -> None:
    """Sanity check: the harness must see the bundled templates."""
    assert TEMPLATES, (
        "No templates discovered under templates/. Either the templates root "
        "moved or _local_templates_root() can no longer find it."
    )


@pytest.mark.parametrize(
    ("type_name", "template_name", "template_dir"),
    TEMPLATES,
    ids=[f"{t}/{n}" for t, n, _ in TEMPLATES],
)
def test_template_renders_without_unrendered_jinja(
    type_name: str,
    template_name: str,
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """Each template must render with its defaults and leave no Jinja markers."""
    patched = _patch_template_for_test(template_dir, tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(
        template=str(patched),
        output_dir=str(out_dir),
        no_input=True,
    )

    generated = next(p for p in out_dir.iterdir() if p.is_dir())

    pyproject = generated / "pyproject.toml"
    assert pyproject.is_file(), f"missing pyproject.toml in {generated}"
    pyproject_text = pyproject.read_text(encoding="utf-8")
    assert "{{" not in pyproject_text, (
        f"unrendered Jinja in {pyproject}: contains '{{{{' — a cookiecutter "
        "variable was referenced but not substituted."
    )
    pyproject_data = tomllib.loads(pyproject_text)
    assert pyproject_data["project"]["name"]
    dependencies = pyproject_data["project"].get("dependencies", [])
    assert isinstance(dependencies, list)
    if (type_name, template_name) == ("bub", "default"):
        _assert_bub_default_dependencies(dependencies, pyproject_data)

    lifecycle = generated / ".agentseek" / "lifecycle.toml"
    assert lifecycle.is_file(), f"missing .agentseek/lifecycle.toml in {generated}"
    lifecycle_text = lifecycle.read_text(encoding="utf-8")
    assert "{{" not in lifecycle_text, (
        f"unrendered Jinja in {lifecycle}: contains '{{{{' — a cookiecutter "
        "variable was referenced but not substituted."
    )
    lifecycle_data = tomllib.loads(lifecycle_text)
    assert lifecycle_data["version"] == 1, f"{type_name}/{template_name} must retain lifecycle version 1"
    assert lifecycle_data["template"] == f"{type_name}/{template_name}"
    assert lifecycle_data["processes"]
    assert not (generated / "duties.py").exists()
    assert "backend" not in lifecycle_data.get("tasks", {})
    readme_text = (generated / "README.md").read_text(encoding="utf-8")
    assert "agentseek task backend" not in readme_text
    _assert_dependency_sync_task(type_name, template_name, generated, lifecycle_data)
    if (type_name, template_name) in seekdb_skill_templates:
        _assert_seekdb_skill_task(generated, lifecycle_data)

    if (type_name, template_name) == ("langchain", "default"):
        _assert_langchain_default_template(generated)

    if (type_name, template_name) in rag_host_binding_templates:
        _assert_rag_template_host_binding(
            generated,
            check_frontend_env=(type_name, template_name) == ("langchain", "agentic-rag-openvino"),
        )

    if (type_name, template_name) == ("deepagents", "content-builder"):
        _assert_deepagents_content_builder_template(generated)

    if (type_name, template_name) == ("deepagents", "default"):
        _assert_deepagents_default_template(generated)

    if (type_name, template_name) in language_instruction_templates:
        _assert_language_instruction_template(generated)

    if (type_name, template_name) == ("langchain", "agentic-rag-openvino"):
        _assert_agentic_rag_openvino_template(generated)

    if (type_name, template_name) == ("langchain", "agentic-rag-hybrid"):
        _assert_agentic_rag_hybrid_template(generated, lifecycle_data)

    _assert_frontend_package_json(generated)


@pytest.mark.parametrize(
    ("type_name", "template_name", "template_dir"),
    TEMPLATES,
    ids=[f"{t}/{n}" for t, n, _ in TEMPLATES],
)
def test_template_lifecycle_commands_smoke(
    type_name: str,
    template_name: str,
    template_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rendered templates expose the AgentSeek lifecycle commands."""
    patched = _patch_template_for_test(template_dir, tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(
        template=str(patched),
        output_dir=str(out_dir),
        no_input=True,
    )

    generated = next(p for p in out_dir.iterdir() if p.is_dir())
    assert (generated / ".agentseek" / "lifecycle.toml").is_file()
    monkeypatch.chdir(generated)

    app = build_command_app()
    runner = CliRunner()

    info = runner.invoke(app, ["info"])
    assert info.exit_code == 0, info.stdout + info.stderr
    assert f"Template: {type_name}/{template_name}" in info.stdout

    if (type_name, template_name) in dependency_sync_templates:
        task_calls: list[tuple[list[str], Path]] = []

        def record_task(command: Sequence[str], *, project, cwd: str) -> int:
            task_calls.append((list(command), project.root / cwd))
            return 0

        monkeypatch.setattr("agentseek.cli.lifecycle.core._run_command", record_task)

        sync = runner.invoke(app, ["task", "sync"])
        assert sync.exit_code == 0, sync.stdout + sync.stderr
        assert task_calls == [(["uv", "sync"], generated)]

        backend = runner.invoke(app, ["task", "backend"])
        assert backend.exit_code == 1
        assert "Unknown lifecycle task: backend" in backend.stderr

    dev = runner.invoke(app, ["dev", "--dry-run", "--skip-check"])
    assert dev.exit_code == 0, dev.stdout + dev.stderr
    assert "Startup plan" in dev.stdout
