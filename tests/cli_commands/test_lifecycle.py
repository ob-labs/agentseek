from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
env_file = ".env"

[tools]
required = ["python"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_MODEL]
required = true
default = "openai:gpt-4o-mini"

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]

[services.app]
url = "http://127.0.0.1:5173"

[processes.web]
command = ["python", "-m", "http.server", "5173"]
cwd = "."

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
    assert "ok   frontend/node_modules: frontend/node_modules is present." in result.stdout
    assert "ok   BUB_MODEL: BUB_MODEL is configured." in result.stdout


def test_doctor_reports_missing_required_inputs(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--strict"])

    assert result.exit_code == 1
    assert "fail .env: .env is missing." in result.stdout
    assert "fail BUB_API_KEY: BUB_API_KEY or BUB_OPENAI_API_KEY is not configured." in result.stdout
    assert "fail frontend/node_modules: frontend/node_modules is missing." in result.stdout


def test_doctor_live_accepts_2xx_and_3xx_statuses(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    _write_project_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)

    class FakeResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

    for status_code in (200, 204, 301, 302):
        monkeypatch.setattr(
            "agentseek.cli.lifecycle.core.httpx.get",
            lambda *args, status_code=status_code, **kwargs: FakeResponse(status_code),
        )
        result = CliRunner().invoke(build_command_app(), ["doctor", "--live"])

        assert result.exit_code == 0, result.stdout + result.stderr
        assert "ok   app: http://127.0.0.1:5173 is reachable." in result.stdout


def test_doctor_live_rejects_4xx_and_5xx_statuses(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    _write_project_inputs(tmp_path)
    monkeypatch.chdir(tmp_path)

    class FakeResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

    for status_code in (400, 404, 500):
        monkeypatch.setattr(
            "agentseek.cli.lifecycle.core.httpx.get",
            lambda *args, status_code=status_code, **kwargs: FakeResponse(status_code),
        )
        result = CliRunner().invoke(build_command_app(), ["doctor", "--live"])

        assert result.exit_code == 1
        assert "fail app: http://127.0.0.1:5173 is not reachable." in result.stdout


def test_dev_dry_run_dispatches_lifecycle_spec(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--dry-run"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Startup plan" in result.stdout
    assert "Web: python -m http.server 5173" in result.stdout
    assert "App: http://127.0.0.1:5173" in result.stdout


def test_dev_skip_check_still_enforces_required_inputs(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])

    assert result.exit_code == 2
    assert "Project is not ready to run." in result.stderr
    assert "fail .env: .env is missing." in result.stdout
    assert "fail BUB_API_KEY: BUB_API_KEY or BUB_OPENAI_API_KEY is not configured." in result.stdout


def test_dev_skip_check_help_describes_preliminary_doctor_pass() -> None:
    result = CliRunner().invoke(build_command_app(), ["dev", "--help"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "preliminary strict doctor pass" in result.stdout


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


def test_task_reports_missing_cwd(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    spec_path = tmp_path / ".agentseek" / "lifecycle.toml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8")
        + """

[tasks.missing_cwd]
description = "Run from a missing directory."
command = ["__PYTHON__", "-c", "print('unreachable')"]
cwd = "missing-dir"
""".replace("__PYTHON__", sys.executable),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "missing_cwd"])

    assert result.exit_code == 2
    assert "Lifecycle task 'missing_cwd' cwd is missing: missing-dir." in result.stderr
    assert "update [tasks.missing_cwd].cwd" in result.stderr


def test_task_does_not_pass_env_file_to_child_process(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    (tmp_path / ".env").write_text(
        "BUB_MODEL=dotenv-model\nBUB_OPENAI_API_KEY=dotenv-key\nEXTRA_DOTENV=hidden\n",
        encoding="utf-8",
    )
    captured_env_kwarg: object = None

    def fake_call(command: object, *, cwd: object, **kwargs: Any) -> int:
        nonlocal captured_env_kwarg
        del command, cwd
        captured_env_kwarg = kwargs.get("env")
        return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_MODEL", "shell-model")
    monkeypatch.setenv("BUB_OPENAI_API_KEY", "shell-key")
    monkeypatch.setattr("agentseek.cli.lifecycle.core.subprocess.call", fake_call)

    result = CliRunner().invoke(build_command_app(), ["task", "version"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert captured_env_kwarg is None


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
