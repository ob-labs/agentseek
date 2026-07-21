from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import agentseek.cli.lifecycle.core as lifecycle_core
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

[services.seekdb]
url = "mysql://127.0.0.1:2884/phoenix"

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


def _write_v2_lifecycle_spec(
    root: Path,
    *,
    env_file: str | None = None,
    required_path: str | None = None,
    process_cwd: str = ".",
    task_cwd: str = ".",
) -> None:
    spec_dir = root / ".agentseek"
    spec_dir.mkdir()
    env_file_line = f'env_file = "{env_file}"\n' if env_file is not None else ""
    required_paths = f'required = ["{required_path}"]' if required_path is not None else "required = []"
    (spec_dir / "lifecycle.toml").write_text(
        f"""
version = 2
template = "test/operational-paths"
name = "Operational Paths"
{env_file_line}
[paths]
{required_paths}

[env.API_KEY]
required = true

[processes.web]
command = ["{sys.executable}", "-c", "print('unreachable')"]
cwd = "{process_cwd}"

[tasks.run]
description = "Run a marker task."
command = ["{sys.executable}", "-c", "print('unreachable')"]
cwd = "{task_cwd}"
""".lstrip(),
        encoding="utf-8",
    )


def _swap_with_outside_symlink(path: Path, outside: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            if child.is_dir():
                _remove_tree(child)
            else:
                child.unlink()
        path.rmdir()
    else:
        path.unlink()
    path.symlink_to(outside, target_is_directory=outside.is_dir())


def _remove_tree(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            _remove_tree(child)
        else:
            child.unlink()
    path.rmdir()


def _swap_after_lifecycle_load(monkeypatch, path: Path, outside: Path) -> None:
    original = lifecycle_core.load_lifecycle_project

    def load_and_swap(root: Path | None = None):
        project = original(root)
        _swap_with_outside_symlink(path, outside)
        return project

    for command in ("info", "doctor", "dev", "task"):
        monkeypatch.setattr(f"agentseek.cli.commands.{command}.load_lifecycle_project", load_and_swap)


def _assert_confined_rejection(result, escaped: Path, field: str) -> None:
    assert result.exit_code == 2, result.stdout + result.stderr
    assert f"Invalid lifecycle {field} path." in result.stderr
    assert str(escaped) not in result.stdout + result.stderr


def _spy_resolved_path_access(monkeypatch, method: str) -> list[Path]:
    original = getattr(Path, method)
    accessed: list[Path] = []

    def record(self: Path, *args: object, **kwargs: object):
        accessed.append(self.resolve(strict=False))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, method, record)
    return accessed


def test_info_dispatches_lifecycle_spec(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--verbose"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Lifecycle spec: " in result.stdout
    assert ".agentseek/lifecycle.toml" in result.stdout
    assert "Template: test/default" in result.stdout
    assert "Name: Spec Project" in result.stdout
    assert "seekdb: mysql://127.0.0.1:2884/phoenix" in result.stdout
    assert "Seekdb:" not in result.stdout
    assert "commands: dev, info, doctor" in result.stdout
    assert "tasks: version" in result.stdout


def test_info_lists_lifecycle_tasks_and_task_discovery_hint(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Lifecycle Tasks" in result.stdout
    assert "version: Write a task marker." in result.stdout
    assert "agentseek task --list" in result.stdout


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


def test_doctor_live_runs_v2_check_through_the_shared_http_path(tmp_path: Path, monkeypatch) -> None:
    spec_dir = tmp_path / ".agentseek"
    spec_dir.mkdir()
    (spec_dir / "lifecycle.toml").write_text(
        f'''\
version = 2
template = "test/live-check"
name = "V2 Live Check"

[services.app]
name = "App"
kind = "web"
url = "http://127.0.0.1:8080"
primary = true
description = "Application."

[processes.app]
command = ["{sys.executable}", "-c", "print('unreachable')"]
provides = ["app"]

[checks.app]
target = "http://127.0.0.1:8080/health"
service = "app"
''',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    class FakeResponse:
        status_code = 204

    requested: list[tuple[str, float]] = []

    def get(url: str, *, timeout: float) -> FakeResponse:
        requested.append((url, timeout))
        return FakeResponse()

    monkeypatch.setattr("agentseek.cli.lifecycle.core.httpx.get", get)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert requested == [("http://127.0.0.1:8080/health", 2.0)]
    assert "ok   app: http://127.0.0.1:8080/health is reachable." in result.stdout


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
    assert "seekdb: mysql://127.0.0.1:2884/phoenix" in result.stdout
    assert "Seekdb:" not in result.stdout


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


@pytest.mark.parametrize("command", (["info"], ["doctor"]))
def test_v2_operational_path_env_file_symlink_swap_rejects_before_file_access(
    tmp_path: Path,
    monkeypatch,
    command: list[str],
) -> None:
    _write_v2_lifecycle_spec(tmp_path, env_file="settings/.env")
    env_dir = tmp_path / "settings"
    env_dir.mkdir()
    (env_dir / ".env").write_text("API_KEY=inside\n", encoding="utf-8")
    outside = tmp_path.parent / f"{tmp_path.name}-outside-env"
    outside.mkdir()
    escaped = outside / ".env"
    escaped.write_text("API_KEY=outside\n", encoding="utf-8")
    _swap_after_lifecycle_load(monkeypatch, env_dir, outside)
    accessed = _spy_resolved_path_access(monkeypatch, "is_file")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), command)

    _assert_confined_rejection(result, escaped, "env_file")
    assert escaped not in accessed


def test_v2_operational_path_dev_env_settings_symlink_swap_rejects_before_reader(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, env_file="settings/.env")
    env_dir = tmp_path / "settings"
    env_dir.mkdir()
    (env_dir / ".env").write_text("API_KEY=inside\n", encoding="utf-8")
    outside = tmp_path.parent / f"{tmp_path.name}-outside-env-settings"
    outside.mkdir()
    escaped = outside / ".env"
    escaped.write_text("API_KEY=outside\n", encoding="utf-8")
    _swap_after_lifecycle_load(monkeypatch, env_dir, outside)
    read_paths: list[Path | None] = []

    def record_settings(project, *, env_file: Path | None, defaults: bool) -> dict[str, str]:
        del project, defaults
        read_paths.append(env_file)
        return {}

    monkeypatch.setattr(lifecycle_core, "_env_file_checks", lambda project: [])
    monkeypatch.setattr(lifecycle_core, "_env_settings_values", record_settings)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])

    _assert_confined_rejection(result, escaped, "env_file")
    assert read_paths == [None]


@pytest.mark.parametrize("command", (["doctor"], ["dev", "--skip-check"]))
def test_v2_operational_path_required_symlink_swap_rejects_before_exists(
    tmp_path: Path,
    monkeypatch,
    command: list[str],
) -> None:
    _write_v2_lifecycle_spec(tmp_path, required_path="inputs/required.txt")
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "required.txt").write_text("inside\n", encoding="utf-8")
    outside = tmp_path.parent / f"{tmp_path.name}-outside-required"
    outside.mkdir()
    escaped = outside / "required.txt"
    escaped.write_text("outside\n", encoding="utf-8")
    _swap_after_lifecycle_load(monkeypatch, inputs, outside)
    accessed = _spy_resolved_path_access(monkeypatch, "exists")
    popen_called = False

    def fail_popen(*args: object, **kwargs: object):
        nonlocal popen_called
        del args, kwargs
        popen_called = True
        raise AssertionError

    monkeypatch.setattr(lifecycle_core.subprocess, "Popen", fail_popen)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), command)

    _assert_confined_rejection(result, escaped, "paths.required")
    assert not popen_called
    assert escaped not in accessed


def test_v2_operational_path_process_cwd_symlink_swap_after_load_rejects_before_popen(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, process_cwd="runtime")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-process-load"
    outside.mkdir()
    _swap_after_lifecycle_load(monkeypatch, runtime, outside)
    popen_called = False

    def fail_popen(*args: object, **kwargs: object):
        nonlocal popen_called
        del args, kwargs
        popen_called = True
        raise AssertionError

    monkeypatch.setattr(lifecycle_core.subprocess, "Popen", fail_popen)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])

    _assert_confined_rejection(result, outside, "processes.web.cwd")
    assert not popen_called


def test_v2_operational_path_process_cwd_symlink_swap_after_readiness_rejects_before_popen(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, process_cwd="runtime")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-process-ready"
    outside.mkdir()
    original = lifecycle_core._ensure_required_inputs

    def ensure_then_swap(project) -> None:
        original(project)
        _swap_with_outside_symlink(runtime, outside)

    popen_called = False

    def fail_popen(*args: object, **kwargs: object):
        nonlocal popen_called
        del args, kwargs
        popen_called = True
        raise AssertionError

    monkeypatch.setattr(lifecycle_core, "_ensure_required_inputs", ensure_then_swap)
    monkeypatch.setattr(lifecycle_core.subprocess, "Popen", fail_popen)
    monkeypatch.setenv("API_KEY", "inside")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])

    _assert_confined_rejection(result, outside, "processes.web.cwd")
    assert not popen_called


def test_v2_operational_path_task_cwd_symlink_swap_rejects_before_subprocess_call(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, task_cwd="tasks")
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-task"
    outside.mkdir()
    _swap_after_lifecycle_load(monkeypatch, tasks, outside)
    call_called = False

    def fail_call(*args: object, **kwargs: object) -> int:
        nonlocal call_called
        del args, kwargs
        call_called = True
        raise AssertionError

    monkeypatch.setattr(lifecycle_core.subprocess, "call", fail_call)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), ["task", "run"])

    _assert_confined_rejection(result, outside, "tasks.run.cwd")
    assert not call_called


def test_v2_operational_path_task_cwd_symlink_swap_after_check_rejects_before_subprocess_call(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, task_cwd="tasks")
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-task-race"
    outside.mkdir()
    original_is_dir = Path.is_dir
    checked = False
    call_called = False

    def swap_after_check(path: Path) -> bool:
        nonlocal checked
        result = original_is_dir(path)
        if path == tasks and not checked:
            checked = True
            _swap_with_outside_symlink(tasks, outside)
        return result

    def fail_call(*args: object, **kwargs: object) -> int:
        nonlocal call_called
        del args, kwargs
        call_called = True
        raise AssertionError

    monkeypatch.setattr(Path, "is_dir", swap_after_check)
    monkeypatch.setattr(lifecycle_core.subprocess, "call", fail_call)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), ["task", "run"])

    assert checked
    _assert_confined_rejection(result, outside, "tasks.run.cwd")
    assert not call_called


def test_v2_operational_path_preflights_all_process_cwds_before_starting_children(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_lifecycle_spec(tmp_path, process_cwd="first")
    spec_path = tmp_path / ".agentseek" / "lifecycle.toml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8")
        + f'''
[processes.worker]
command = ["{sys.executable}", "-c", "print('unreachable')"]
cwd = "second"
''',
        encoding="utf-8",
    )
    (tmp_path / "first").mkdir()
    second = tmp_path / "second"
    second.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-process-preflight"
    outside.mkdir()
    original = lifecycle_core._ensure_required_inputs
    sentinel_ran = False
    calls: list[object] = []

    def ensure_then_swap(project) -> None:
        nonlocal sentinel_ran
        original(project)
        sentinel_ran = True
        _swap_with_outside_symlink(second, outside)

    def record_popen(*args: object, **kwargs: object):
        calls.append((args, kwargs))
        raise AssertionError

    monkeypatch.setattr(lifecycle_core, "_ensure_required_inputs", ensure_then_swap)
    monkeypatch.setattr(lifecycle_core.subprocess, "Popen", record_popen)
    monkeypatch.setenv("API_KEY", "inside")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])

    assert sentinel_ran
    _assert_confined_rejection(result, outside, "processes.worker.cwd")
    assert calls == []


def test_v1_path_compatibility_keeps_runtime_joins_and_symlinks(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle_spec(tmp_path)
    _write_project_inputs(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-v1"
    outside.mkdir()
    (outside / "package.json").write_text("{}\n", encoding="utf-8")
    (outside / "required.txt").write_text("required\n", encoding="utf-8")
    outside_env = outside / "outside.env"
    outside_env.write_text("BUB_MODEL=outside\n", encoding="utf-8")
    _swap_with_outside_symlink(tmp_path / "frontend", outside)
    spec_path = tmp_path / ".agentseek" / "lifecycle.toml"
    spec_path.write_text(
        spec_path
        .read_text(encoding="utf-8")
        .replace('env_file = ".env"', f'env_file = "{outside_env}"')
        .replace(
            'required = ["frontend/package.json", "frontend/node_modules"]',
            f'required = ["../{outside.name}/required.txt"]',
        )
        .replace('cwd = "."\n\n[checks.app]', f'cwd = "../{outside.name}"\n\n[checks.app]')
        + 'cwd = "frontend"\n',
        encoding="utf-8",
    )
    project = lifecycle_core.discover_lifecycle_project(tmp_path)
    required = lifecycle_core._path_checks(project)
    env_file = lifecycle_core._env_file_path(project)
    process = project.spec.processes["web"]
    task = project.spec.tasks["version"]
    seen: list[Path] = []

    def fake_call(command: object, *, cwd: Path, **kwargs: object) -> int:
        del command, kwargs
        seen.append(cwd)
        return 0

    monkeypatch.setattr(lifecycle_core.subprocess, "call", fake_call)
    monkeypatch.setattr(
        lifecycle_core.subprocess,
        "Popen",
        lambda command, *, cwd, start_new_session: seen.append(Path(cwd)),
    )
    monkeypatch.delenv("BUB_MODEL", raising=False)
    assert required[0].status == "ok"
    assert env_file == outside_env
    assert lifecycle_core._env_requirement_source(project, "BUB_MODEL", project.spec.env["BUB_MODEL"]) == str(
        outside_env
    )
    assert lifecycle_core._resolve_operational_path(project, process.cwd, allow_dot=True) == tmp_path / process.cwd
    assert lifecycle_core._run_command(task.command, project=project, cwd=task.cwd) == 0
    lifecycle_core._spawn_process(process, project=project)
    assert seen == [tmp_path / "frontend", tmp_path / f"../{outside.name}"]


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
