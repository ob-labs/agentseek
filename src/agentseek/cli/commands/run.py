"""``agentseek run`` — start the project locally and open the frontend.

The command runs in the user's project working directory:

1. Loads ``.env`` (must exist) via ``pydantic-settings`` to read ``PORT``.
2. Detects launch mode: docker compose, Python entry point, or explicit override.
3. Spawns the service as a child process inheriting the current environment.
4. Polls the frontend URL until it's ready (or times out).
5. Opens the default browser to that URL.
6. Streams the child until the user hits Ctrl-C, then tears down cleanly.

Each child process reads ``.env`` on its own (docker compose loads it
automatically; Python entry points typically reuse ``pydantic-settings``).
This command therefore never mutates ``os.environ``.
"""

from __future__ import annotations

import contextlib
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from pydantic import AliasChoices, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class DevMode(StrEnum):
    AUTO = "auto"
    COMPOSE = "compose"
    PYTHON = "python"


DEFAULT_PORT = 3000
DEFAULT_HOST = "127.0.0.1"
DEFAULT_WAIT_TIMEOUT = 30
TERMINATE_GRACE_SECONDS = 5

COMPOSE_CANDIDATES: tuple[str, ...] = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
PYTHON_ENTRY_CANDIDATES: tuple[str, ...] = ("app.py", "main.py")
PYTHON_SCRIPT_HINTS: tuple[str, ...] = ("serve", "dev")

app = typer.Typer(
    name="run",
    help="Start the project locally after completing .env configuration.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def run(
    port: Annotated[
        int | None,
        typer.Option("--port", help="Frontend port. Defaults to PORT in .env or 3000.", show_default=False),
    ] = None,
    host: Annotated[
        str,
        typer.Option("--host", help="Host to probe for readiness."),
    ] = DEFAULT_HOST,
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="Skip opening the default browser."),
    ] = False,
    wait_timeout: Annotated[
        int,
        typer.Option("--wait-timeout", help="Seconds to wait for the frontend to become ready."),
    ] = DEFAULT_WAIT_TIMEOUT,
    mode: Annotated[
        DevMode,
        typer.Option("--mode", case_sensitive=False, help="Launch mode override (auto | compose | python)."),
    ] = DevMode.AUTO,
) -> None:
    """Start the project's services and (optionally) open the browser."""
    cwd = Path.cwd()
    settings = _load_settings(cwd)
    resolved_mode = _resolve_mode(mode, cwd)
    resolved_port = port if port is not None else (settings.port or DEFAULT_PORT)
    url = f"http://{host}:{resolved_port}/"

    proc = _start_service(resolved_mode, cwd)
    _install_signal_handlers(proc)
    exit_code = 0
    try:
        ready = _wait_ready(url, wait_timeout, proc)
        if not ready:
            typer.echo(
                f"Frontend at {url} did not become ready within {wait_timeout}s.",
                err=True,
            )
            exit_code = 1
        else:
            _open_browser(url, enabled=not no_browser)
            typer.echo(f"Service ready at {url}. Press Ctrl-C to stop.")
            exit_code = _wait_for_exit(proc)
    finally:
        _shutdown(proc, resolved_mode, cwd)
    raise typer.Exit(exit_code)


# ---------------------------------------------------------------------------
# .env handling
# ---------------------------------------------------------------------------


class DevSettings(BaseSettings):
    """Settings sourced from ``.env`` (and overridden by process env vars).

    Only the knobs ``agentseek run`` cares about are declared here. ``.env`` may
    contain other keys for the project itself; those are ignored at this layer
    and remain visible to child processes through their own configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    port: int | None = Field(
        default=None,
        validation_alias=AliasChoices("PORT", "FRONTEND_PORT"),
    )


def _load_settings(cwd: Path) -> DevSettings:
    """Load :class:`DevSettings` from ``cwd/.env``. Exit 2 on missing/invalid input."""
    env_path = cwd / ".env"
    if not env_path.is_file():
        typer.echo(
            f"Missing .env file at {env_path}.\n"
            "Copy .env.example to .env and fill in the required values, then retry `agentseek run`.",
            err=True,
        )
        raise typer.Exit(2)
    # ``DevSettings`` resolves ``env_file=".env"`` against the current working
    # directory, which the caller has already set to ``cwd``.
    try:
        return DevSettings()
    except ValidationError as exc:
        typer.echo(f"Invalid configuration in {env_path}:\n{exc}", err=True)
        raise typer.Exit(2) from exc


# ---------------------------------------------------------------------------
# Mode detection & service spawn
# ---------------------------------------------------------------------------


def _resolve_mode(requested: DevMode, cwd: Path) -> DevMode:
    if requested is not DevMode.AUTO:
        return requested
    detected = _detect_mode(cwd)
    if detected is None:
        typer.echo(
            "Could not auto-detect a runnable project layout.\n"
            "Expected one of: docker-compose.yml / compose.yaml at the project root, "
            "or pyproject.toml plus an app.py/main.py entry point or a `serve`/`dev` script.\n"
            "Pass --mode compose|python to override.",
            err=True,
        )
        raise typer.Exit(2)
    return detected


def _detect_mode(cwd: Path) -> DevMode | None:
    if any((cwd / name).is_file() for name in COMPOSE_CANDIDATES):
        return DevMode.COMPOSE
    if (cwd / "pyproject.toml").is_file() and _has_python_entry(cwd):
        return DevMode.PYTHON
    return None


def _has_python_entry(cwd: Path) -> bool:
    if any((cwd / name).is_file() for name in PYTHON_ENTRY_CANDIDATES):
        return True
    return _has_script_hint(cwd / "pyproject.toml")


def _has_script_hint(pyproject: Path) -> bool:
    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return _find_script_hint(content) is not None


def _find_script_hint(content: str) -> str | None:
    for hint in PYTHON_SCRIPT_HINTS:
        if re.search(rf"(?m)^\s*{re.escape(hint)}\s*=", content):
            return hint
        if f'"{hint}"' in content or f"'{hint}'" in content:
            return hint
    return None


def _start_service(mode: DevMode, cwd: Path) -> subprocess.Popen[bytes]:
    if mode is DevMode.COMPOSE:
        return _start_compose(cwd)
    if mode is DevMode.PYTHON:
        return _start_python(cwd)
    msg = f"Unsupported dev mode: {mode}"  # auto should already be resolved.
    raise RuntimeError(msg)


def _start_compose(cwd: Path) -> subprocess.Popen[bytes]:
    docker = shutil.which("docker")
    if docker is None:
        typer.echo(
            "`docker` was not found on PATH. Install Docker Desktop (or the docker CLI) to use compose mode.",
            err=True,
        )
        raise typer.Exit(2)
    cmd = [docker, "compose", "up"]
    return _spawn(cmd, cwd)


def _start_python(cwd: Path) -> subprocess.Popen[bytes]:
    uv = shutil.which("uv")
    if uv is not None:
        target = _python_target(cwd)
        cmd: list[str] = [uv, "run", *target]
    else:
        target = _python_target(cwd)
        cmd = [sys.executable, *target]
    return _spawn(cmd, cwd)


def _python_target(cwd: Path) -> list[str]:
    for name in PYTHON_ENTRY_CANDIDATES:
        if (cwd / name).is_file():
            return [name]
    if _has_script_hint(cwd / "pyproject.toml"):
        content = (cwd / "pyproject.toml").read_text(encoding="utf-8")
        if hint := _find_script_hint(content):
            return [hint]
    msg = "No Python entry point detected."
    raise RuntimeError(msg)


def _spawn(cmd: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    typer.echo(f"$ {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(cwd))  # noqa: S603


# ---------------------------------------------------------------------------
# Readiness, browser, shutdown
# ---------------------------------------------------------------------------


def _wait_ready(url: str, timeout: int, proc: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + max(timeout, 0)
    while True:
        if _probe(url):
            return True
        if proc.poll() is not None:
            return False
        if time.monotonic() >= deadline:
            return False
        time.sleep(1.0)


def _probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2.0) as resp:  # noqa: S310 (loopback URL)
            status = getattr(resp, "status", 200)
            return 200 <= status < 500
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def _open_browser(url: str, *, enabled: bool) -> None:
    if not enabled:
        return
    try:
        webbrowser.open(url)
    except webbrowser.Error as exc:
        typer.echo(f"Could not open browser automatically: {exc}", err=True)


def _wait_for_exit(proc: subprocess.Popen[bytes]) -> int:
    try:
        return proc.wait()
    except KeyboardInterrupt:
        return 130


def _shutdown(proc: subprocess.Popen[bytes], mode: DevMode, cwd: Path) -> None:
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        try:
            proc.wait(timeout=TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=TERMINATE_GRACE_SECONDS)
    if mode is DevMode.COMPOSE:
        _compose_down(cwd)


def _compose_down(cwd: Path) -> None:
    docker = shutil.which("docker")
    if docker is None:
        return
    with contextlib.suppress(subprocess.TimeoutExpired, OSError):
        subprocess.run(  # noqa: S603
            [docker, "compose", "down"],
            cwd=str(cwd),
            check=False,
            timeout=30,
        )


def _install_signal_handlers(proc: subprocess.Popen[bytes]) -> None:
    def _handler(signum: int, _frame: object) -> None:
        with contextlib.suppress(ProcessLookupError):
            proc.send_signal(signal.SIGTERM)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Not in main thread or unsupported platform — ignore.
            continue


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_WAIT_TIMEOUT",
    "DevMode",
    "DevSettings",
    "app",
]
