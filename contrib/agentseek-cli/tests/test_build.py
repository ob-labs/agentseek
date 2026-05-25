"""Tests for ``agentseek build``."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest
from agentseek_cli.app import build_app
from agentseek_cli.commands import build as build_module
from typer.testing import CliRunner


def _make_dockerfile(directory: Path) -> Path:
    dockerfile = directory / "Dockerfile"
    dockerfile.write_text("FROM scratch\n")
    return dockerfile


# --- Pure helpers --------------------------------------------------------------


def test_default_tag_inferred_from_cwd_name(tmp_path: Path) -> None:
    project = tmp_path / "My Cool Project"
    project.mkdir()
    assert build_module._resolve_tag(project, None) == "my-cool-project:latest"


def test_explicit_tag_overrides_default(tmp_path: Path) -> None:
    assert build_module._resolve_tag(tmp_path, "demo:1.0") == "demo:1.0"


def test_resolve_dockerfile_returns_path_when_present(tmp_path: Path) -> None:
    dockerfile = _make_dockerfile(tmp_path)
    assert build_module._resolve_dockerfile(tmp_path, None) == dockerfile


def test_build_command_single_platform_uses_plain_build(tmp_path: Path) -> None:
    dockerfile = _make_dockerfile(tmp_path)
    cmd = build_module._build_command(
        tag="demo:1.0",
        dockerfile=dockerfile,
        context=tmp_path,
        platforms=["linux/amd64"],
        no_cache=False,
        build_args=[],
    )
    assert cmd[:2] == ["docker", "build"]
    assert "buildx" not in cmd
    assert "--platform" in cmd and "linux/amd64" in cmd


def test_build_command_multi_platform_uses_buildx(tmp_path: Path) -> None:
    dockerfile = _make_dockerfile(tmp_path)
    cmd = build_module._build_command(
        tag="demo:multi",
        dockerfile=dockerfile,
        context=tmp_path,
        platforms=["linux/amd64", "linux/arm64"],
        no_cache=True,
        build_args=["FOO=bar", "BAZ=qux"],
    )
    assert cmd[:3] == ["docker", "buildx", "build"]
    assert "--no-cache" in cmd
    assert cmd.count("--build-arg") == 2
    assert "FOO=bar" in cmd and "BAZ=qux" in cmd
    platform_idx = cmd.index("--platform")
    assert cmd[platform_idx + 1] == "linux/amd64,linux/arm64"


# --- CLI integration -----------------------------------------------------------


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _make_dockerfile(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_no_dockerfile_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_app(), ["build", "--dry-run"])
    assert result.exit_code == 2
    assert "Dockerfile" in result.stderr


def test_dry_run_prints_command_no_subprocess(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: dict[str, object] = {"ran": False}

    def _fail(*args: object, **kwargs: object) -> None:
        called["ran"] = True
        raise AssertionError("subprocess.run should not be called in dry-run")  # noqa: TRY003

    monkeypatch.setattr(subprocess, "run", _fail)

    result = CliRunner().invoke(
        build_app(),
        ["build", "--dry-run", "--tag", "demo:1.0"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "docker build" in result.stdout
    assert "demo:1.0" in result.stdout
    assert called["ran"] is False


def test_build_args_forwarded(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: None)
    result = CliRunner().invoke(
        build_app(),
        [
            "build",
            "--dry-run",
            "--tag",
            "demo:1.0",
            "--build-arg",
            "FOO=bar",
            "--build-arg",
            "BAZ=qux",
        ],
    )
    assert result.exit_code == 0
    assert "--build-arg FOO=bar" in result.stdout
    assert "--build-arg BAZ=qux" in result.stdout


def test_platform_list_uses_buildx(project: Path) -> None:
    result = CliRunner().invoke(
        build_app(),
        [
            "build",
            "--dry-run",
            "--platform",
            "linux/amd64,linux/arm64",
            "--tag",
            "demo:multi",
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "docker buildx build" in result.stdout
    assert "linux/amd64,linux/arm64" in result.stdout


def test_push_flag_invokes_push_after_build(project: Path) -> None:
    result = CliRunner().invoke(
        build_app(),
        ["build", "--dry-run", "--push", "--tag", "demo:1.0"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert any(line.startswith("docker build") for line in lines)
    assert any(line.startswith("docker push demo:1.0") for line in lines)


def test_missing_docker_exits_1(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil as _shutil

    monkeypatch.setattr(_shutil, "which", lambda _name: None)

    result = CliRunner().invoke(
        build_app(),
        ["build", "--tag", "demo:1.0"],
    )
    assert result.exit_code == 1
    assert "docker" in result.stderr.lower()


def test_real_subprocess_invocation_returncode_propagates(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Sequence[str]] = {}

    class _CP:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def _fake_run(cmd, check=False):
        captured["cmd"] = list(cmd)
        return _CP(7)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/bin/docker")

    result = CliRunner().invoke(
        build_app(),
        ["build", "--tag", "demo:1.0"],
    )
    assert result.exit_code == 7
    assert captured["cmd"][:3] == ["docker", "build", "-t"]
