"""Local dev supervisor: gateway + ctx server + frontend."""

from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import signal
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path

import typer

DEFAULT_AGENT_URL = "http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent"
DEFAULT_FRONTEND_PORT = "{{ cookiecutter.frontend_port }}"
DEFAULT_COPILOTKIT_PORT = "{{ cookiecutter.copilotkit_port }}"
DEFAULT_CTX_SERVER_PORT = "{{ cookiecutter.ctx_server_port }}"
SHUTDOWN_GRACE_SECONDS = 10


def _require_binary(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        typer.echo(f"Required executable {name!r} was not found on PATH.", err=True)
        raise typer.Exit(2)
    return resolved


def _project_root() -> Path:
    return Path.cwd()


def _frontend_dir(root: Path) -> Path:
    return root / "frontend"


def _build_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("AGENTSEEK_STREAM_OUTPUT", "true")
    env.setdefault("AGENTSEEK_AG_UI_PORT", "{{ cookiecutter.gateway_port }}")
    env.setdefault("FRONTEND_PORT", DEFAULT_FRONTEND_PORT)
    env.setdefault("COPILOTKIT_PORT", DEFAULT_COPILOTKIT_PORT)
    env.setdefault("AGENTSEEK_AG_UI_AGENT_URL", DEFAULT_AGENT_URL)
    env.setdefault("CTX_SERVER_PORT", DEFAULT_CTX_SERVER_PORT)
    env.setdefault("PWD", str(root))
    return env


def _spawn(cmd: list[str], *, cwd: Path, env: Mapping[str, str]) -> subprocess.Popen[bytes]:
    rendered = " ".join(shlex.quote(part) for part in cmd)
    typer.echo(f"$ {rendered}")
    return subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(cwd),
        env=dict(env),
        start_new_session=True,
    )


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + SHUTDOWN_GRACE_SECONDS
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.2)
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)


def _validate_frontend(frontend_dir: Path) -> None:
    if not (frontend_dir / "package.json").is_file():
        typer.echo(f"Missing frontend package.json at {frontend_dir}.", err=True)
        raise typer.Exit(2)
    if not (frontend_dir / "node_modules").is_dir():
        typer.echo(
            "Frontend dependencies are missing. Run `npm install --prefix frontend` first.",
            err=True,
        )
        raise typer.Exit(2)


def _run_seed(env: Mapping[str, str], root: Path) -> None:
    """Run maybe_seed() once before starting the servers."""
    typer.echo("Checking ContextSeek store for seed data...")
    try:
        subprocess.run(  # noqa: S603
            ["python", "-c", "from {{ cookiecutter.project_slug }}.seed import maybe_seed; maybe_seed()"],
            cwd=str(root),
            env=dict(env),
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        typer.echo(f"Seed step failed (exit {exc.returncode}); continuing anyway.", err=True)


def main() -> None:
    root = _project_root()
    frontend_dir = _frontend_dir(root)
    _validate_frontend(frontend_dir)

    env = _build_env(root)
    npm = _require_binary("npm")

    _run_seed(env, root)

    ctx_port = env.get("CTX_SERVER_PORT", DEFAULT_CTX_SERVER_PORT)
    gateway = _spawn(["agentseek", "gateway", "--enable-channel", "ag-ui"], cwd=root, env=env)
    ctx_server = _spawn(
        [
            "uvicorn",
            "{{ cookiecutter.project_slug }}.server:app",
            "--host", "127.0.0.1",
            "--port", ctx_port,
        ],
        cwd=root,
        env=env,
    )
    frontend = _spawn([npm, "run", "dev"], cwd=frontend_dir, env=env)

    procs = [gateway, ctx_server, frontend]

    def _shutdown(*_args: object) -> None:
        for p in reversed(procs):
            _terminate(p)
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _shutdown)

    try:
        while True:
            codes = [p.poll() for p in procs]
            if any(c is not None for c in codes):
                for p in reversed(procs):
                    _terminate(p)
                raise SystemExit(next(c for c in codes if c is not None) or 0)
            time.sleep(1.0)
    finally:
        for p in reversed(procs):
            _terminate(p)
