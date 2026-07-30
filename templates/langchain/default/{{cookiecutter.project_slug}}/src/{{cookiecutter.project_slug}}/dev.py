"""Local dev supervisor for the LangChain AG-UI template."""

from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import signal
import subprocess
import time
from collections.abc import Generator, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import typer

from .process_group import ManagedProcess, manage, spawn_kwargs, terminate

DEFAULT_AGENT_URL = "http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent"
DEFAULT_FRONTEND_PORT = "{{ cookiecutter.frontend_port }}"
DEFAULT_COPILOTKIT_PORT = "{{ cookiecutter.copilotkit_port }}"
DEFAULT_LANGCHAIN_SPEC = "{{ cookiecutter.project_slug }}.demo_binding:build_spec"
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
    env.setdefault("BUB_STREAM_OUTPUT", "true")
    env.setdefault("BUB_AG_UI_PORT", "{{ cookiecutter.gateway_port }}")
    env.setdefault("FRONTEND_PORT", DEFAULT_FRONTEND_PORT)
    env.setdefault("COPILOTKIT_PORT", DEFAULT_COPILOTKIT_PORT)
    env.setdefault("BUB_AG_UI_AGENT_URL", DEFAULT_AGENT_URL)
    env.setdefault("BUB_LANGCHAIN_SPEC", DEFAULT_LANGCHAIN_SPEC)
    env.setdefault("PWD", str(root))
    return env


def _spawn(cmd: list[str], *, cwd: Path, env: Mapping[str, str]) -> ManagedProcess:
    rendered = " ".join(shlex.quote(part) for part in cmd)
    typer.echo(f"$ {rendered}")
    popen = cast("Any", subprocess.Popen)
    child = cast("subprocess.Popen[bytes]", popen(  # noqa: S603
        cmd,
        cwd=str(cwd),
        env=dict(env),
        **spawn_kwargs(),
    ))
    return manage(child)


def _terminate(proc: ManagedProcess) -> None:
    terminate(proc, grace_seconds=SHUTDOWN_GRACE_SECONDS)


def _terminate_all(processes: list[ManagedProcess]) -> None:
    for process in processes:
        with contextlib.suppress(OSError):
            _terminate(process)


def _validate_frontend(frontend_dir: Path) -> None:
    if not (frontend_dir / "package.json").is_file():
        typer.echo(f"Missing frontend package.json at {frontend_dir}.", err=True)
        raise typer.Exit(2)
    if not (frontend_dir / "node_modules").is_dir():
        typer.echo(
            "Frontend dependencies are missing. Run `agentseek task frontend` first.",
            err=True,
        )
        raise typer.Exit(2)


def main() -> None:
    root = _project_root()
    frontend_dir = _frontend_dir(root)
    _validate_frontend(frontend_dir)

    env = _build_env(root)
    npm = _require_binary("npm")

    processes: list[ManagedProcess] = []
    with _supervise_processes(processes):
        gateway = _spawn(["bub", "gateway", "--enable-channel", "ag-ui"], cwd=root, env=env)
        processes.append(gateway)
        frontend = _spawn([npm, "run", "dev"], cwd=frontend_dir, env=env)
        processes.append(frontend)

        while True:
            gateway_code = gateway.poll()
            frontend_code = frontend.poll()
            if gateway_code is not None or frontend_code is not None:
                raise SystemExit(gateway_code or frontend_code or 0)
            time.sleep(1.0)


@contextlib.contextmanager
def _supervise_processes(processes: Sequence[ManagedProcess]) -> Generator[None, None, None]:
    def _shutdown(*_args: object) -> None:
        raise SystemExit(0)

    previous_handlers: list[tuple[int, object]] = []

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers.append((sig, signal.signal(sig, _shutdown)))
        yield
    finally:
        try:
            for sig, _handler in reversed(previous_handlers):
                signal.signal(sig, signal.SIG_IGN)
            _terminate_all(list(reversed(processes)))
        finally:
            for sig, handler in reversed(previous_handlers):
                signal.signal(sig, cast(Any, handler))
