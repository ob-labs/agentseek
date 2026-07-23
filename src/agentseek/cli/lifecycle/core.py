"""Project lifecycle execution for AgentSeek-managed templates."""

from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import httpx
import typer
from duty import Collection
from duty._internal.collection import Duty
from pydantic import AliasChoices, Field, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict

from agentseek.cli.lifecycle.errors import (
    LifecycleNotFoundError,
    LifecycleTomlError,
    LifecycleValidationError,
    LifecycleVersionUnsupportedError,
    exit_project_error,
)
from agentseek.cli.lifecycle.safety import UnsafeProjectPathError, resolve_confined_project_path
from agentseek.cli.lifecycle.spec import (
    LIFECYCLE_SPEC_FILE,
    REQUIRED_COMMANDS,
    SUPPORTED_LIFECYCLE_VERSION,
    AuthoredLifecycleSpec,
    CheckV1,
    CheckV2,
    EnvRequirement,
    LifecycleSpecV2,
    ProcessV1,
    ProcessV2,
    TaskV1,
    TaskV2,
    read_lifecycle_spec,
)


@dataclass(frozen=True)
class LifecycleProject:
    """Loaded lifecycle definition for a generated project."""

    root: Path
    path: Path
    metadata: dict[str, object]
    spec: AuthoredLifecycleSpec


@dataclass(frozen=True)
class CheckResult:
    status: str
    name: str
    detail: str
    fix: str = ""


class _UnsafeOperationalPathError(UnsafeProjectPathError):
    """A runtime confinement failure tagged only with its lifecycle field."""

    def __init__(self, field: str) -> None:
        super().__init__()
        self.field = field


def discover_lifecycle_project(root: Path | None = None) -> LifecycleProject:
    """Discover and load a lifecycle spec without producing CLI output."""
    project_root = (root or Path.cwd()).resolve()
    discovered = _discover_spec(project_root)
    if discovered is None:
        raise LifecycleNotFoundError(f"Add {LIFECYCLE_SPEC_FILE}.")  # noqa: TRY003
    lifecycle_root, spec_path = discovered
    spec = read_lifecycle_spec(spec_path, project_root=lifecycle_root)
    return LifecycleProject(
        root=lifecycle_root,
        path=spec_path,
        metadata={"version": spec.version, "template": spec.template},
        spec=spec,
    )


def load_lifecycle_project(root: Path | None = None) -> LifecycleProject:
    """Discover and load a lifecycle spec, preserving legacy CLI errors."""
    project_root = (root or Path.cwd()).resolve()
    try:
        return discover_lifecycle_project(project_root)
    except LifecycleNotFoundError as exc:
        exit_project_error(f"Missing AgentSeek lifecycle spec from {project_root} upward.", exc.legacy_detail)
    except LifecycleTomlError as exc:
        exit_project_error("Invalid AgentSeek lifecycle TOML.", exc.legacy_detail)
    except (LifecycleValidationError, LifecycleVersionUnsupportedError) as exc:
        exit_project_error("Invalid AgentSeek lifecycle spec.", exc.legacy_detail)


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
    try:
        task.run(**kwargs)
    except _UnsafeOperationalPathError as exc:
        exit_project_error(
            f"Invalid lifecycle {exc.field} path.",
            f"Update {exc.field} in {LIFECYCLE_SPEC_FILE}.",
        )


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
    except _UnsafeOperationalPathError as exc:
        exit_project_error(
            f"Invalid lifecycle {exc.field} path.",
            f"Update {exc.field} in {LIFECYCLE_SPEC_FILE}.",
        )
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
    for name, task in project.spec.tasks.items():
        collection.add(Duty(name=name, description=task.description, function=_task_function(project, name, task)))
    return collection


def _task_function(project: LifecycleProject, name: str, task: TaskV1 | TaskV2):
    def run_task(_ctx: object) -> None:
        cwd = _operational_path(project, task.cwd, allow_dot=True, field=f"tasks.{name}.cwd")
        if not cwd.is_dir():
            exit_project_error(
                f"Lifecycle task {name!r} cwd is missing: {task.cwd}.",
                f"Create {task.cwd} or update [tasks.{name}].cwd in {LIFECYCLE_SPEC_FILE}.",
            )
        code = _run_command(task.command, project=project, cwd=task.cwd)
        if code:
            raise SystemExit(code)

    run_task.__name__ = f"{name}_task"
    return run_task


def _display_name(name: str) -> str:
    if name == "seekdb":
        return name
    return name.title()


def print_info(project: LifecycleProject, *, verbose: bool) -> None:
    """Print a project summary derived from the lifecycle spec."""
    spec = project.spec
    print("Project")
    print(f"  Root: {project.root}")
    print(f"  Name: {spec.name}")
    print(f"  Template: {spec.template}")
    print(f"  Lifecycle: {spec.path.relative_to(project.root)} / version {spec.version}")
    print()
    print("Entrypoints")
    print("  Dev: agentseek dev")
    for name, service in spec.services.items():
        print(f"  {_display_name(name)}: {service.url}")
    print()
    print("Environment")
    if spec.env_file:
        env_file = _operational_path(project, spec.env_file, allow_dot=False, field="env_file")
        present = env_file.is_file()
        print(f"  Env file: {spec.env_file} ({'present' if present else 'missing'})")
    for name, requirement in spec.env.items():
        source = _env_requirement_source(project, name, requirement)
        print(f"  {name}: {f'set ({source})' if source else 'missing'}")
    print()
    if spec.tasks:
        print("Lifecycle Tasks")
        for name, task in spec.tasks.items():
            print(f"  {name}: {task.description}")
        print()
    print("Next")
    if spec.tasks:
        print("  agentseek task --list")
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
    for name, process in project.spec.processes.items():
        print(f"  {_display_name(name)}: {_render_command(process.command)}")
    for name, service in project.spec.services.items():
        print(f"  {_display_name(name)}: {service.url}")
    if dry_run:
        return

    _ensure_required_inputs(project)
    for name, process in project.spec.processes.items():
        _operational_path(project, process.cwd, allow_dot=True, field=f"processes.{name}.cwd")
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for process in project.spec.processes.values():
            processes.append(_spawn_process(process, project=project))
    except Exception:
        for started_process in processes:
            _terminate(started_process)
        raise
    _wait_for_processes(processes)


def _discover_spec(root: Path) -> tuple[Path, Path] | None:
    for candidate in (root, *root.parents):
        path = candidate / LIFECYCLE_SPEC_FILE
        if path.is_file():
            return candidate, path
    return None


def _static_checks(project: LifecycleProject) -> list[CheckResult]:
    checks = [
        _check("ok" if project.path.is_file() else "fail", project.path.name, "Lifecycle spec is present."),
    ]
    checks.extend(_tool_checks(project.spec.required_tools))
    checks.extend(_path_checks(project))
    checks.extend(_env_file_checks(project))
    checks.extend(_env_checks(project))
    checks.extend(_process_cwd_checks(project))
    return checks


def _tool_checks(tools: Sequence[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name in tools:
        found = shutil.which(name) is not None
        results.append(
            _check(
                "ok" if found else "fail",
                name,
                f"{name} is available." if found else f"{name} is missing.",
                f"Install {name} and make sure it is on PATH.",
            )
        )
    return results


def _path_checks(project: LifecycleProject) -> list[CheckResult]:
    results: list[CheckResult] = []
    for path in project.spec.required_paths:
        operational_path = _operational_path(project, path, allow_dot=False, field="paths.required")
        found = operational_path.exists()
        results.append(
            _check(
                "ok" if found else "fail",
                path,
                f"{path} is present." if found else f"{path} is missing.",
                f"Create {path} or run the setup task declared by this template.",
            )
        )
    return results


def _env_file_checks(project: LifecycleProject) -> list[CheckResult]:
    if project.spec.env_file is None:
        return []
    env_file = _operational_path(project, project.spec.env_file, allow_dot=False, field="env_file")
    present = env_file.is_file()
    return [
        _check(
            "ok" if present else "fail",
            project.spec.env_file,
            f"{project.spec.env_file} is present." if present else f"{project.spec.env_file} is missing.",
            f"Create {project.spec.env_file} or remove env_file from the lifecycle spec.",
        )
    ]


def _env_checks(project: LifecycleProject) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, requirement in project.spec.env.items():
        configured = _env_requirement_source(project, name, requirement) is not None
        if not requirement.required and not configured:
            continue
        status = "ok" if configured else ("fail" if requirement.required else "ok")
        keys = " or ".join(requirement.keys(name))
        results.append(
            _check(
                status,
                name,
                f"{keys} is configured." if configured else f"{keys} is not configured.",
                _env_fix(project, keys),
            )
        )
    return results


def _env_fix(project: LifecycleProject, keys: str) -> str:
    if project.spec.env_file:
        return f"Set {keys} in {project.spec.env_file} or the shell environment."
    return f"Set {keys} in the shell environment."


def _process_cwd_checks(project: LifecycleProject) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, process in project.spec.processes.items():
        cwd = _operational_path(project, process.cwd, allow_dot=True, field=f"processes.{name}.cwd")
        present = cwd.is_dir()
        results.append(
            _check(
                "ok" if present else "fail",
                f"{name} cwd",
                f"{process.cwd} is present." if present else f"{process.cwd} is missing.",
            )
        )
    return results


def _live_checks(project: LifecycleProject) -> list[CheckResult]:
    return [_run_check(name, check) for name, check in project.spec.checks.items()]


def _run_check(name: str, check: CheckV1 | CheckV2) -> CheckResult:
    for _attempt in range(max(check.attempts, 1)):
        ok = _check_target(check)
        if ok:
            return _check("ok", name, f"{check.target} is reachable.")
        time.sleep(0.2)
    return _check("fail", name, f"{check.target} is not reachable.", "Start the local app with `agentseek dev`.")


def _check_target(check: CheckV1 | CheckV2) -> bool:
    try:
        response = httpx.get(check.target, timeout=check.timeout)
    except httpx.HTTPError:
        return False
    return 200 <= response.status_code < 400


def _ensure_required_inputs(project: LifecycleProject) -> None:
    failing = [item for item in _static_checks(project) if item.status == "fail"]
    if failing:
        _print_checks(failing)
        exit_project_error("Project is not ready to run.", "Fix failing checks or use `agentseek doctor` for details.")


def _env_requirement_source(project: LifecycleProject, name: str, requirement: EnvRequirement) -> str | None:
    environment = _env_settings_values(project, env_file=None, defaults=False)
    if environment.get(name):
        return "environment"
    env_file = _env_settings_values(project, env_file=_env_file_path(project), defaults=False)
    if env_file.get(name):
        return project.spec.env_file or "env_file"
    if requirement.default:
        return "default"
    return None


def _env_settings_values(project: LifecycleProject, *, env_file: Path | None, defaults: bool) -> dict[str, str]:
    settings = _env_settings_class(project, defaults=defaults)(_env_file=env_file)
    return settings.model_dump(by_alias=True, exclude_none=True)


def _env_settings_class(project: LifecycleProject, *, defaults: bool) -> type[BaseSettings]:

    class EnvSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    fields: dict[str, Any] = {}
    for name, requirement in project.spec.env.items():
        field_name = f"env_{len(fields)}"
        fields[field_name] = (
            str | None,
            Field(
                requirement.default if defaults else None,
                validation_alias=_env_validation_alias(name, requirement),
                serialization_alias=name,
            ),
        )

    return cast("type[BaseSettings]", create_model("LifecycleEnvSettings", __base__=EnvSettings, **fields))


def _env_validation_alias(name: str, requirement: EnvRequirement) -> str | AliasChoices:
    if not requirement.aliases:
        return name
    return AliasChoices(name, *requirement.aliases)


def _env_file_path(project: LifecycleProject) -> Path | None:
    if project.spec.env_file is None:
        return None
    return _operational_path(project, project.spec.env_file, allow_dot=False, field="env_file")


def _resolve_operational_path(project: LifecycleProject, value: str, *, allow_dot: bool) -> Path:
    """Resolve a runtime lifecycle path while preserving v1 joins."""
    if isinstance(project.spec, LifecycleSpecV2):
        return resolve_confined_project_path(project.root, value, allow_dot=allow_dot)
    return project.root / value


def _operational_path(project: LifecycleProject, value: str, *, allow_dot: bool, field: str) -> Path:
    try:
        return _resolve_operational_path(project, value, allow_dot=allow_dot)
    except UnsafeProjectPathError:
        raise _UnsafeOperationalPathError(field) from None


def _process_cwd_field(project: LifecycleProject, process: ProcessV1 | ProcessV2) -> str:
    for name, candidate in project.spec.processes.items():
        if candidate is process:
            return f"processes.{name}.cwd"
    for name, candidate in project.spec.processes.items():
        if candidate == process:
            return f"processes.{name}.cwd"
    return "process cwd"


def _task_cwd_field(project: LifecycleProject, command: Sequence[str], cwd: str) -> str:
    for name, task in project.spec.tasks.items():
        if task.command is command and task.cwd == cwd:
            return f"tasks.{name}.cwd"
    for name, task in project.spec.tasks.items():
        if task.command == tuple(command) and task.cwd == cwd:
            return f"tasks.{name}.cwd"
    return "task cwd"


def _render_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _spawn_process(process: ProcessV1 | ProcessV2, *, project: LifecycleProject) -> subprocess.Popen[bytes]:
    executable = shutil.which(process.command[0])
    if executable is None:
        exit_project_error(
            f"Missing executable: {process.command[0]}.",
            f"Install {process.command[0]} and make sure it is on PATH.",
        )
    command = (executable, *process.command[1:])
    print(f"$ {_render_command(command)}")
    cwd = _operational_path(project, process.cwd, allow_dot=True, field=_process_cwd_field(project, process))
    return subprocess.Popen(  # noqa: S603
        command,
        cwd=str(cwd),
        start_new_session=True,
    )


def _run_command(command: Sequence[str], *, project: LifecycleProject, cwd: str) -> int:
    executable = shutil.which(command[0])
    if executable is None:
        exit_project_error(
            f"Missing executable: {command[0]}.",
            f"Install {command[0]} and make sure it is on PATH.",
        )
    operational_cwd = _operational_path(
        project,
        cwd,
        allow_dot=True,
        field=_task_cwd_field(project, command, cwd),
    )
    return subprocess.call((executable, *command[1:]), cwd=operational_cwd)  # noqa: S603


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
    for name in project.spec.required_tools:
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
    "discover_lifecycle_project",
    "lifecycle_spec_exists",
    "load_lifecycle_project",
    "run_lifecycle_task",
    "run_task_cli",
]
