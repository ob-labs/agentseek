from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

from tests.cli_commands.helpers import build_command_app


def _write_lifecycle_spec(root: Path) -> None:
    spec_dir = root / ".agentseek"
    spec_dir.mkdir()
    (spec_dir / "lifecycle.toml").write_text(
        """
version = 1
template = "test/default"
name = "Spec Project"

[tools]
required = ["python"]
optional = []

[paths]
required = ["frontend/package.json", "frontend/node_modules"]
optional = []

[env.BUB_MODEL]
required = true

[env.BUB_API_KEY]
required = false
secret = true
aliases = ["BUB_OPENAI_API_KEY"]

[services.app]
url = "http://127.0.0.1:5173"

[processes.web]
command = ["python", "-m", "http.server", "5173"]
cwd = "."
env = { TEST_PROCESS = "true" }

[checks.app]
type = "http"
target = "http://127.0.0.1:5173"

[tasks.version]
description = "Write a task marker."
command = ["__PYTHON__", "-c", "from pathlib import Path; Path('task.done').write_text('ok', encoding='utf-8')"]
""".lstrip().replace("__PYTHON__", sys.executable),
        encoding="utf-8",
    )


def _write_project_inputs(root: Path) -> None:
    (root / "pyproject.toml").write_text('[project]\nname = "spec-project"\nversion = "0.1.0"\n', encoding="utf-8")
    (root / ".env").write_text("BUB_MODEL=openai:gpt-4o-mini\nBUB_OPENAI_API_KEY=test-key\n", encoding="utf-8")
    frontend = root / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("{}\n", encoding="utf-8")
    (frontend / "node_modules").mkdir()


def test_info_dispatches_lifecycle_spec(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--verbose"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Lifecycle spec: " in result.stdout
    assert ".agentseek/lifecycle.toml" in result.stdout
    assert "Template: test/default" in result.stdout
    assert "Name: Spec Project" in result.stdout
    assert "commands: dev, info, doctor" in result.stdout
    assert "tasks: version" in result.stdout


def test_doctor_dispatches_lifecycle_spec(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    _write_project_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--strict"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "ok   lifecycle.toml: Lifecycle spec is present." in result.stdout
    assert "ok   pyproject.toml: Python project file is present." in result.stdout
    assert "ok   frontend/node_modules: frontend/node_modules is present." in result.stdout
    assert "ok   BUB_MODEL: BUB_MODEL is configured." in result.stdout


def test_doctor_reports_missing_required_inputs(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--strict"])

    assert result.exit_code == 1
    assert "fail .env: .env is missing." in result.stdout
    assert "fail frontend/node_modules: frontend/node_modules is missing." in result.stdout


def test_dev_dry_run_dispatches_lifecycle_spec(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--dry-run"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Startup plan" in result.stdout
    assert "Web: python -m http.server 5173" in result.stdout
    assert "App: http://127.0.0.1:5173" in result.stdout


def test_task_lists_spec_tasks(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "--list"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "version" in result.stdout
    assert "Write a task marker." in result.stdout


def test_task_runs_declared_command(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "version"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert (tmp_path / "task.done").read_text(encoding="utf-8") == "ok"


def test_lifecycle_spec_is_inherited_from_parent(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    child = tmp_path / "src" / "nested"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)

    result = CliRunner().invoke(build_command_app(), ["info"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Root: " in result.stdout
    assert str(tmp_path) in result.stdout


def test_missing_lifecycle_file_exits_2(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--dry-run"])

    assert result.exit_code == 2
    assert "Missing AgentSeek lifecycle spec" in result.stderr
