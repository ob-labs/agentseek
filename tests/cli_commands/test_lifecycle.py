from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from tests.cli_commands.helpers import build_command_app


def _write_duties(path: Path) -> None:
    path.write_text(
        """
from duty import duty

AGENTSEEK = {"version": 1, "template": "test/default"}


@duty
def dev(ctx, dry_run=False):
    print(f"dev: {dry_run=}")


@duty
def info(ctx, verbose=False):
    print(f"info: {verbose=}")


@duty
def doctor(ctx, live=False, strict=False):
    print(f"doctor: {live=} {strict=}")


@duty
def echo(ctx, name="world", loud=False):
    message = f"hello {name}"
    print(message.upper() if loud else message)
""".lstrip(),
        encoding="utf-8",
    )


def test_dev_runs_doctor_then_dev(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "doctor: live=False strict=True" in result.stdout
    assert "dev: dry_run=False" in result.stdout


def test_dev_dry_run_skips_strict_doctor(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--dry-run"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "doctor:" not in result.stdout
    assert "dev: dry_run=True" in result.stdout


def test_info_dispatches_lifecycle_task(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "info: verbose=False" in result.stdout


def test_doctor_dispatches_lifecycle_task(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--strict"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "doctor: live=True strict=True" in result.stdout


def test_task_forwards_to_duty_cli(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "echo", "name=psi", "loud=true"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "HELLO PSI" in result.stdout


def test_task_coerces_false_bool_kwargs(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "doctor", "live=false", "strict=false"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "doctor: live=False strict=False" in result.stdout


def test_task_lists_project_duties(tmp_path: Path, monkeypatch) -> None:
    _write_duties(tmp_path / "duties.py")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["task", "--list"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "echo" in result.stdout


def test_missing_lifecycle_file_exits_2(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["dev", "--dry-run"])

    assert result.exit_code == 2
    assert "Missing duties.py" in result.stderr
