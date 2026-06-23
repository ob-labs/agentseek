"""Lifecycle spec loading."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentseek.cli.lifecycle.errors import exit_project_error

SUPPORTED_LIFECYCLE_VERSION = 1
LIFECYCLE_SPEC_FILE = ".agentseek/lifecycle.toml"
REQUIRED_COMMANDS: tuple[str, ...] = ("dev", "info", "doctor")


@dataclass(frozen=True)
class EnvRequirement:
    name: str
    required: bool = False
    secret: bool = False
    description: str = ""
    aliases: tuple[str, ...] = ()

    @property
    def keys(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class Service:
    name: str
    url: str


@dataclass(frozen=True)
class Process:
    name: str
    command: tuple[str, ...]
    cwd: str = "."
    env: dict[str, str] | None = None
    shutdown_grace_seconds: int = 10


@dataclass(frozen=True)
class Check:
    name: str
    type: str
    target: str
    required: bool = True
    timeout_seconds: float = 2.0
    attempts: int = 1
    wait_seconds: float = 0.0


@dataclass(frozen=True)
class Task:
    name: str
    command: tuple[str, ...]
    cwd: str = "."
    description: str = ""


@dataclass(frozen=True)
class LifecycleSpec:
    path: Path
    version: int
    template: str
    name: str
    tools: dict[str, bool]
    paths: dict[str, bool]
    env: dict[str, EnvRequirement]
    services: dict[str, Service]
    processes: dict[str, Process]
    checks: dict[str, Check]
    tasks: dict[str, Task]


def load_lifecycle_spec(path: Path) -> LifecycleSpec:
    """Load and validate a lifecycle spec from TOML."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    version = _int_value(data, "version", default=0)
    if version != SUPPORTED_LIFECYCLE_VERSION:
        exit_project_error(
            f"Unsupported AgentSeek lifecycle spec version: {version!r}.",
            f"This AgentSeek release supports version {SUPPORTED_LIFECYCLE_VERSION}.",
        )

    spec = LifecycleSpec(
        path=path,
        version=version,
        template=_str_value(data, "template"),
        name=_str_value(data, "name", default=_str_value(data, "project_name")),
        tools=_tools(data.get("tools", {})),
        paths=_required_optional(data.get("paths", {})),
        env=_env(data.get("env", {})),
        services=_services(data.get("services", {})),
        processes=_processes(data.get("processes", {})),
        checks=_checks(data.get("checks", {})),
        tasks=_tasks(data.get("tasks", {})),
    )
    _validate_spec(spec)
    return spec


def _validate_spec(spec: LifecycleSpec) -> None:
    if not spec.name:
        exit_project_error("Invalid AgentSeek lifecycle spec.", "Set `name` in .agentseek/lifecycle.toml.")
    if not spec.processes:
        exit_project_error("Invalid AgentSeek lifecycle spec.", "Declare at least one process under [processes].")


def _tools(raw: object) -> dict[str, bool]:
    return _required_optional(raw)


def _required_optional(raw: object) -> dict[str, bool]:
    table = _mapping(raw)
    values: dict[str, bool] = {}
    for name in _str_sequence(table.get("required", ())):
        values[name] = True
    for name in _str_sequence(table.get("optional", ())):
        values.setdefault(name, False)
    return values


def _env(raw: object) -> dict[str, EnvRequirement]:
    requirements: dict[str, EnvRequirement] = {}
    for name, value in _mapping(raw).items():
        if isinstance(value, bool):
            requirements[name] = EnvRequirement(name=name, required=value)
            continue
        table = _mapping(value)
        requirements[name] = EnvRequirement(
            name=name,
            required=_bool_value(table, "required", default=False),
            secret=_bool_value(table, "secret", default=False),
            description=_str_value(table, "description"),
            aliases=tuple(_str_sequence(table.get("aliases", ()))),
        )
    return requirements


def _services(raw: object) -> dict[str, Service]:
    services: dict[str, Service] = {}
    for name, value in _mapping(raw).items():
        if isinstance(value, str):
            services[name] = Service(name=name, url=value)
            continue
        table = _mapping(value)
        services[name] = Service(name=name, url=_str_value(table, "url"))
    return services


def _processes(raw: object) -> dict[str, Process]:
    processes: dict[str, Process] = {}
    for name, value in _mapping(raw).items():
        table = _mapping(value)
        command = tuple(_str_sequence(table.get("command", ())))
        if not command:
            continue
        processes[name] = Process(
            name=name,
            command=command,
            cwd=_str_value(table, "cwd", default="."),
            env=_string_table(table.get("env", {})) or None,
            shutdown_grace_seconds=_int_value(table, "shutdown_grace_seconds", default=10),
        )
    return processes


def _checks(raw: object) -> dict[str, Check]:
    checks: dict[str, Check] = {}
    for name, value in _mapping(raw).items():
        table = _mapping(value)
        checks[name] = Check(
            name=name,
            type=_str_value(table, "type", default="tcp"),
            target=_str_value(table, "url", default=_str_value(table, "target")),
            required=_bool_value(table, "required", default=True),
            timeout_seconds=_float_value(table, "timeout", default=2.0),
            attempts=_int_value(table, "attempts", default=1),
            wait_seconds=_float_value(table, "wait", default=0.0),
        )
    return checks


def _tasks(raw: object) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for name, value in _mapping(raw).items():
        table = _mapping(value)
        command = tuple(_str_sequence(table.get("command", ())))
        if not command:
            continue
        tasks[name] = Task(
            name=name,
            command=command,
            cwd=_str_value(table, "cwd", default="."),
            description=_str_value(table, "description"),
        )
    return tasks


def _mapping(raw: object) -> Mapping[str, Any]:
    return raw if isinstance(raw, dict) else {}


def _string_table(raw: object) -> dict[str, str]:
    return {key: str(value) for key, value in _mapping(raw).items()}


def _str_sequence(raw: object) -> Sequence[str]:
    if isinstance(raw, list | tuple):
        return tuple(str(item) for item in raw)
    return ()


def _str_value(raw: Mapping[str, Any], key: str, *, default: str = "") -> str:
    return str(raw.get(key, default))


def _int_value(raw: Mapping[str, Any], key: str, *, default: int) -> int:
    try:
        return int(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def _float_value(raw: Mapping[str, Any], key: str, *, default: float) -> float:
    try:
        return float(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def _bool_value(raw: Mapping[str, Any], key: str, *, default: bool) -> bool:
    value = raw.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


__all__ = [
    "LIFECYCLE_SPEC_FILE",
    "REQUIRED_COMMANDS",
    "SUPPORTED_LIFECYCLE_VERSION",
    "Check",
    "EnvRequirement",
    "LifecycleSpec",
    "Process",
    "Service",
    "Task",
    "load_lifecycle_spec",
]
