"""Project lifecycle execution for AgentSeek-managed templates."""

from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import textwrap
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import typer
from duty import Collection
from duty._internal.collection import Duty

from agentseek.cli.lifecycle.errors import exit_project_error
from agentseek.cli.lifecycle.spec import (
    LIFECYCLE_SPEC_FILE,
    REQUIRED_COMMANDS,
    SUPPORTED_LIFECYCLE_VERSION,
    Check,
    EnvRequirement,
    LifecycleSpec,
    Process,
    Task,
    load_lifecycle_spec,
)


@dataclass(frozen=True)
class LifecycleProject:
    """Loaded lifecycle definition for a generated project."""

    root: Path
    path: Path
    metadata: dict[str, object]
    spec: LifecycleSpec


@dataclass(frozen=True)
class CheckResult:
    status: str
    name: str
    detail: str
    fix: str = ""


def load_lifecycle_project(root: Path | None = None) -> LifecycleProject:
    """Discover and load a lifecycle spec from *root* or its parents."""
    project_root = (root or Path.cwd()).resolve()
    discovered = _discover_spec(project_root)
    if discovered is None:
        exit_project_error(
            f"Missing AgentSeek lifecycle spec from {project_root} upward.",
            f"Add {LIFECYCLE_SPEC_FILE}.",
        )
    lifecycle_root, spec_path = discovered
    spec = load_lifecycle_spec(spec_path)
    return LifecycleProject(
        root=lifecycle_root,
        path=spec_path,
        metadata={"version": spec.version, "template": spec.template},
        spec=spec,
    )


def lifecycle_spec_exists(root: Path | None = None) -> bool:
    """Return whether a lifecycle spec can be discovered from *root* upward."""
    project_root = (root or Path.cwd()).resolve()
    return _discover_spec(project_root) is not None


def run_lifecycle_task(project: LifecycleProject, name: str, **kwargs: object) -> None:
    """Run a first-class lifecycle command."""
    collection = _lifecycle_collection(project)
    try:
        task = collection.get(name)
    except KeyError:
        exit_project_error(
            f"Unknown AgentSeek lifecycle command: {name}.",
            f"Expected one of: {', '.join(REQUIRED_COMMANDS)}.",
        )
    task.run(**kwargs)


def run_task_cli(project: LifecycleProject, args: list[str]) -> int:
    """Run project-defined tasks declared in the lifecycle spec."""
    collection = _task_collection(project)
    if not args:
        _print_task_help(project)
        return 1
    if args[0] in {"--list", "-l"}:
        print(textwrap.indent(collection.format_help(), prefix="  "))
        return 0
    if args[0] in {"--help", "-h"}:
        _print_task_help(project)
        return 0
    try:
        task = collection.get(args[0])
    except KeyError:
        typer.echo(f"Unknown lifecycle task: {args[0]}", err=True)
        return 1
    if len(args) > 1:
        typer.echo("Lifecycle spec tasks do not accept extra arguments yet.", err=True)
        return 1
    try:
        task.run()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def _lifecycle_collection(project: LifecycleProject) -> Collection:
    collection = Collection(str(project.path))
    collection.add(
        Duty(
            name="info",
            description="Print project summary.",
            function=lambda _ctx, verbose=False: print_info(project, verbose=verbose),
        )
    )
    collection.add(
        Duty(
            name="doctor",
            description="Check local project readiness.",
            function=lambda _ctx, live=False, strict=False: doctor(project, live=live, strict=strict),
        )
    )
    collection.add(
        Duty(
            name="dev",
            description="Run local development.",
            function=lambda _ctx, dry_run=False: dev(project, dry_run=dry_run),
        )
    )
    return collection


def _task_collection(project: LifecycleProject) -> Collection:
    collection = Collection(str(project.path))
    for task in project.spec.tasks.values():
        collection.add(Duty(name=task.name, description=task.description, function=_task_function(project, task)))
    return collection


def _task_function(project: LifecycleProject, task: Task):
    def run_task(_ctx: object) -> None:
        code = _run_command(task.command, cwd=project.root / task.cwd, env=os.environ)
        if code:
            raise SystemExit(code)

    run_task.__name__ = f"{task.name}_task"
    return run_task


def print_info(project: LifecycleProject, *, verbose: bool) -> None:
    """Print a project summary derived from the lifecycle spec."""
    env = _env_values(project.root)
    spec = project.spec
    print("Project")
    print(f"  Root: {project.root}")
    print(f"  Name: {spec.name}")
    print(f"  Template: {spec.template}")
    print(f"  Lifecycle: {spec.path.relative_to(project.root)} / version {spec.version}")
    print()
    print("Entrypoints")
    print("  Dev: agentseek dev")
    for service in spec.services.values():
        print(f"  {service.name.title()}: {service.url}")
    print()
    print("Environment")
    print(f"  .env: {'present' if (project.root / '.env').is_file() else 'missing'}")
    for requirement in spec.env.values():
        print(f"  {requirement.name}: {'set' if _env_requirement_configured(env, requirement) else 'missing'}")
    print()
    print("Next")
    print("  agentseek doctor")
    print("  agentseek dev")
    if verbose:
        _print_verbose_info(project)


def doctor(project: LifecycleProject, *, live: bool, strict: bool) -> None:
    """Run local readiness checks derived from the lifecycle spec."""
    results = _static_checks(project)
    if live:
        results.extend(_live_checks(project))
    _print_checks(results)
    has_fail = any(item.status == "fail" for item in results)
    has_warn = any(item.status == "warn" for item in results)
    if has_fail or (strict and has_warn):
        raise SystemExit(1)


def dev(project: LifecycleProject, *, dry_run: bool) -> None:
    """Start local development processes declared in the lifecycle spec."""
    print("Startup plan")
    for process in project.spec.processes.values():
        print(f"  {process.name.title()}: {_render_command(process.command)}")
    for service in project.spec.services.values():
        print(f"  {service.name.title()}: {service.url}")
    if dry_run:
        return

    _ensure_required_inputs(project)
    env = _build_env(project)
    processes = [_spawn_process(process, root=project.root, env=env) for process in project.spec.processes.values()]
    _wait_for_processes(processes)


def _discover_spec(root: Path) -> tuple[Path, Path] | None:
    for candidate in (root, *root.parents):
        path = candidate / LIFECYCLE_SPEC_FILE
        if path.is_file():
            return candidate, path
    return None


def _static_checks(project: LifecycleProject) -> list[CheckResult]:
    env = _env_values(project.root)
    checks = [
        _check("ok" if project.path.is_file() else "fail", project.path.name, "Lifecycle spec is present."),
        _check(
            "ok" if (project.root / "pyproject.toml").is_file() else "fail",
            "pyproject.toml",
            "Python project file is present.",
        ),
    ]
    checks.extend(_tool_checks(project.spec.tools))
    checks.extend(_path_checks(project))
    checks.extend(_env_checks(project.spec.env, env))
    checks.extend(_process_cwd_checks(project))
    return checks


def _tool_checks(tools: Mapping[str, bool]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, required in tools.items():
        found = shutil.which(name) is not None
        status = "ok" if found else ("fail" if required else "warn")
        results.append(
            _check(
                status,
                name,
                f"{name} is available." if found else f"{name} is missing.",
                f"Install {name} and make sure it is on PATH.",
            )
        )
    return results


def _path_checks(project: LifecycleProject) -> list[CheckResult]:
    results: list[CheckResult] = []
    for path, required in project.spec.paths.items():
        found = (project.root / path).exists()
        status = "ok" if found else ("fail" if required else "warn")
        results.append(
            _check(
                status,
                path,
                f"{path} is present." if found else f"{path} is missing.",
                f"Create {path} or run the setup task declared by this template.",
            )
        )
    return results


def _env_checks(requirements: Mapping[str, EnvRequirement], env: Mapping[str, str]) -> list[CheckResult]:
    results: list[CheckResult] = [
        _check(
            "ok" if env else "fail",
            ".env",
            ".env is present." if env else ".env is missing.",
            "Run `cp .env.example .env` and fill in required values.",
        )
    ]
    for requirement in requirements.values():
        configured = _env_requirement_configured(env, requirement)
        status = "ok" if configured else ("fail" if requirement.required else "warn")
        keys = " or ".join(requirement.keys)
        results.append(
            _check(
                status,
                requirement.name,
                f"{keys} is configured." if configured else f"{keys} is missing.",
                f"Set {keys} in .env.",
            )
        )
    return results


def _process_cwd_checks(project: LifecycleProject) -> list[CheckResult]:
    results: list[CheckResult] = []
    for process in project.spec.processes.values():
        cwd = project.root / process.cwd
        results.append(
            _check(
                "ok" if cwd.is_dir() else "fail",
                f"{process.name} cwd",
                f"{process.cwd} is present." if cwd.is_dir() else f"{process.cwd} is missing.",
            )
        )
    return results


def _live_checks(project: LifecycleProject) -> list[CheckResult]:
    return [_run_check(check) for check in project.spec.checks.values()]


def _run_check(check: Check) -> CheckResult:
    if check.wait_seconds:
        time.sleep(check.wait_seconds)
    for _attempt in range(max(check.attempts, 1)):
        ok = _check_target(check)
        if ok:
            return _check("ok", check.name, f"{check.target} is reachable.")
        time.sleep(0.2)
    status = "fail" if check.required else "warn"
    return _check(status, check.name, f"{check.target} is not reachable.", "Start the local app with `agentseek dev`.")


def _check_target(check: Check) -> bool:
    parsed = urlparse(check.target)
    if check.type == "http":
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return bool(host) and _tcp_connects(host, port, timeout=check.timeout_seconds)
    if check.type == "tcp":
        host = parsed.hostname or parsed.path.partition(":")[0]
        port_text = str(parsed.port or parsed.path.partition(":")[2])
        return bool(host and port_text.isdigit()) and _tcp_connects(host, int(port_text), timeout=check.timeout_seconds)
    return False


def _ensure_required_inputs(project: LifecycleProject) -> None:
    failing = [item for item in _static_checks(project) if item.status == "fail"]
    if failing:
        _print_checks(failing)
        exit_project_error("Project is not ready to run.", "Fix failing checks or use `agentseek doctor` for details.")


def _build_env(project: LifecycleProject) -> dict[str, str]:
    env = dict(os.environ)
    for process in project.spec.processes.values():
        if process.env:
            env.update(process.env)
    env.setdefault("PWD", str(project.root))
    return env


def _env_values(root: Path) -> dict[str, str]:
    env_path = root / ".env"
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _env_requirement_configured(env: Mapping[str, str], requirement: EnvRequirement) -> bool:
    return any(bool(env.get(key)) for key in requirement.keys)


def _render_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _spawn_process(process: Process, *, root: Path, env: Mapping[str, str]) -> subprocess.Popen[bytes]:
    executable = shutil.which(process.command[0])
    if executable is None:
        exit_project_error(
            f"Missing executable: {process.command[0]}.",
            f"Install {process.command[0]} and make sure it is on PATH.",
        )
    command = (executable, *process.command[1:])
    print(f"$ {_render_command(command)}")
    return subprocess.Popen(  # noqa: S603
        command,
        cwd=str(root / process.cwd),
        env=dict(env),
        start_new_session=True,
    )


def _run_command(command: Sequence[str], *, cwd: Path, env: Mapping[str, str]) -> int:
    executable = shutil.which(command[0])
    if executable is None:
        exit_project_error(
            f"Missing executable: {command[0]}.",
            f"Install {command[0]} and make sure it is on PATH.",
        )
    return subprocess.call((executable, *command[1:]), cwd=cwd, env=dict(env))  # noqa: S603


def _wait_for_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    def _shutdown(*_args: object) -> None:
        for process in processes:
            _terminate(process)
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _shutdown)

    try:
        while True:
            exit_codes = [process.poll() for process in processes]
            finished = [code for code in exit_codes if code is not None]
            if finished:
                for process in processes:
                    _terminate(process)
                raise SystemExit(next(code for code in finished if code is not None) or 0)
            time.sleep(1.0)
    finally:
        for process in processes:
            _terminate(process)


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 10
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.2)
    if process.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def _tcp_connects(host: str, port: int, *, timeout: float) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def _check(status: str, name: str, detail: str, fix: str = "") -> CheckResult:
    return CheckResult(status=status, name=name, detail=detail, fix=fix)


def _print_checks(checks: Sequence[CheckResult]) -> None:
    for item in checks:
        print(f"{item.status:<4} {item.name}: {item.detail}")
        if item.status in {"fail", "warn"} and item.fix:
            print(f"     next: {item.fix}")


def _print_verbose_info(project: LifecycleProject) -> None:
    print()
    print("Capabilities")
    print(f"  commands: {', '.join(REQUIRED_COMMANDS)}")
    print(f"  tasks: {', '.join(project.spec.tasks) or 'none'}")
    print()
    print("Discovery")
    print(f"  Python: {sys.executable}")
    for name in project.spec.tools:
        print(f"  {name}: {shutil.which(name) or 'missing'}")


def _print_task_help(project: LifecycleProject) -> None:
    typer.echo("Usage: agentseek task [TASK]")
    typer.echo()
    typer.echo(f"Lifecycle spec: {project.path}")
    typer.echo()
    typer.echo("Forms:")
    typer.echo("  agentseek task --list")
    typer.echo("  agentseek task <name>")


__all__ = [
    "REQUIRED_COMMANDS",
    "SUPPORTED_LIFECYCLE_VERSION",
    "LifecycleProject",
    "lifecycle_spec_exists",
    "load_lifecycle_project",
    "run_lifecycle_task",
    "run_task_cli",
]
