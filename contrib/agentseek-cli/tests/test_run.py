from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from agentseek_cli.app import build_app
from agentseek_cli.commands import run as run_module
from typer.testing import CliRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakePopen:
    """Minimal Popen-shaped stand-in for tests."""

    def __init__(self, returncode: int = 0, *, stays_alive: bool = False) -> None:
        self._returncode = returncode
        self._stays_alive = stays_alive
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        if self._stays_alive:
            return None
        return self._returncode

    def wait(self, timeout: float | None = None) -> int:
        return self._returncode

    def terminate(self) -> None:
        self.terminated = True
        self._stays_alive = False

    def kill(self) -> None:
        self.killed = True
        self._stays_alive = False

    def send_signal(self, signum: int) -> None:  # noqa: ARG002
        self.terminated = True
        self._stays_alive = False


def _write_env(cwd: Path, **values: str) -> Path:
    env_path = cwd / ".env"
    env_path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    return env_path


def _patch_no_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    """signal.signal needs main thread; tests run in pytest's main thread normally,
    but we still neutralize it so handler installation never fails the assertion path.
    """
    monkeypatch.setattr(run_module, "_install_signal_handlers", lambda proc: None)


# ---------------------------------------------------------------------------
# .env validation
# ---------------------------------------------------------------------------


def test_missing_env_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_app(), ["run"])
    assert result.exit_code == 2
    assert "Missing .env" in result.stderr


# ---------------------------------------------------------------------------
# Mode resolution
# ---------------------------------------------------------------------------


def test_unknown_mode_exits_2_when_auto_cannot_detect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_env(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(build_app(), ["run"])
    assert result.exit_code == 2
    assert "auto-detect" in result.stderr


# ---------------------------------------------------------------------------
# --no-browser path with a happy compose mode
# ---------------------------------------------------------------------------


def test_no_browser_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_env(tmp_path, PORT="4321")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    fake = _FakePopen(returncode=0, stays_alive=False)
    captured: dict[str, Any] = {}

    def fake_spawn(cmd: list[str], cwd: Path, env: dict[str, str]) -> _FakePopen:  # noqa: ARG001
        captured["cmd"] = cmd
        return fake

    browser_calls: list[str] = []

    monkeypatch.setattr(run_module, "_spawn", fake_spawn)
    monkeypatch.setattr(run_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(run_module, "_probe", lambda url: True)
    monkeypatch.setattr(run_module.webbrowser, "open", lambda url: browser_calls.append(url))
    monkeypatch.setattr(run_module, "_compose_down", lambda cwd: None)
    _patch_no_signal(monkeypatch)

    result = CliRunner().invoke(build_app(), ["run", "--no-browser"])

    assert result.exit_code == 0, result.stderr
    assert browser_calls == []
    assert captured["cmd"][:3] == ["/usr/bin/docker", "compose", "up"]
    assert "http://127.0.0.1:4321/" in result.stdout


# ---------------------------------------------------------------------------
# Compose mode invokes docker compose up
# ---------------------------------------------------------------------------


def test_compose_mode_invokes_compose_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_env(tmp_path)
    (tmp_path / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    captured: dict[str, Any] = {}
    fake = _FakePopen(returncode=0, stays_alive=False)

    def fake_spawn(cmd: list[str], cwd: Path, env: dict[str, str]) -> _FakePopen:  # noqa: ARG001
        captured["cmd"] = cmd
        return fake

    monkeypatch.setattr(run_module, "_spawn", fake_spawn)
    monkeypatch.setattr(run_module.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(run_module, "_probe", lambda url: True)
    monkeypatch.setattr(run_module.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(run_module, "_compose_down", lambda cwd: None)
    _patch_no_signal(monkeypatch)

    result = CliRunner().invoke(build_app(), ["run", "--no-browser"])

    assert result.exit_code == 0, result.stderr
    assert captured["cmd"] == ["/bin/docker", "compose", "up"]


# ---------------------------------------------------------------------------
# Readiness timeout exits non-zero
# ---------------------------------------------------------------------------


def test_wait_ready_timeout_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_env(tmp_path)
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    fake = _FakePopen(returncode=0, stays_alive=True)

    def fake_spawn(cmd: list[str], cwd: Path, env: dict[str, str]) -> _FakePopen:  # noqa: ARG001
        return fake

    monkeypatch.setattr(run_module, "_spawn", fake_spawn)
    monkeypatch.setattr(run_module.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(run_module, "_probe", lambda url: False)
    monkeypatch.setattr(run_module, "_compose_down", lambda cwd: None)
    _patch_no_signal(monkeypatch)

    result = CliRunner().invoke(
        build_app(), ["run", "--no-browser", "--wait-timeout", "0"]
    )

    assert result.exit_code == 1
    assert "did not become ready" in result.stderr
    assert fake.terminated is True


# ---------------------------------------------------------------------------
# Mode override: --mode python
# ---------------------------------------------------------------------------


def test_python_mode_picks_app_py_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_env(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hi')\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    captured: dict[str, Any] = {}
    fake = _FakePopen(returncode=0, stays_alive=False)

    def fake_spawn(cmd: list[str], cwd: Path, env: dict[str, str]) -> _FakePopen:  # noqa: ARG001
        captured["cmd"] = cmd
        return fake

    def fake_which(name: str) -> str | None:
        return None  # force fallback to sys.executable

    monkeypatch.setattr(run_module, "_spawn", fake_spawn)
    monkeypatch.setattr(run_module.shutil, "which", fake_which)
    monkeypatch.setattr(run_module, "_probe", lambda url: True)
    monkeypatch.setattr(run_module.webbrowser, "open", lambda url: None)
    _patch_no_signal(monkeypatch)

    result = CliRunner().invoke(
        build_app(), ["run", "--no-browser", "--mode", "python"]
    )

    assert result.exit_code == 0, result.stderr
    assert captured["cmd"] == [sys.executable, "app.py"]
