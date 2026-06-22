"""Project lifecycle loading for AgentSeek-managed templates."""

from __future__ import annotations

import argparse
import sys
import textwrap
from dataclasses import dataclass
from inspect import Parameter, signature
from pathlib import Path
from types import ModuleType
from typing import Any

import typer
from duty import Collection
from duty._internal import cli as duty_cli
from duty._internal.cli import get_parser, parse_commands, print_help, specified_options, split_args
from duty._internal.exceptions import DutyFailure

SUPPORTED_LIFECYCLE_VERSION = 1
LIFECYCLE_FILE = "duties.py"
REQUIRED_TASKS: tuple[str, ...] = ("dev", "info", "doctor")


@dataclass(frozen=True)
class LifecycleProject:
    """Loaded lifecycle definition for a generated project."""

    root: Path
    path: Path
    metadata: dict[str, Any]
    module: ModuleType
    collection: Collection

    def task(self, name: str) -> Any:
        return self.collection.get(name)


def load_lifecycle_project(root: Path | None = None) -> LifecycleProject:
    """Load and validate ``duties.py`` from *root*."""
    project_root = (root or Path.cwd()).resolve()
    lifecycle_path = project_root / LIFECYCLE_FILE
    if not lifecycle_path.is_file():
        _exit_project_error(
            f"Missing {LIFECYCLE_FILE} at {lifecycle_path}.",
            "This project is not adapted to the AgentSeek lifecycle yet.",
        )

    module, collection = _load_collection(lifecycle_path)
    metadata = _load_metadata(module)
    _validate_tasks(collection)
    return LifecycleProject(
        root=project_root,
        path=lifecycle_path,
        metadata=metadata,
        module=module,
        collection=collection,
    )


def run_lifecycle_task(project: LifecycleProject, name: str, **kwargs: Any) -> None:
    """Run a lifecycle task from a loaded project."""
    task = project.task(name)
    if hasattr(task, "run"):
        task.run(**kwargs)
    else:
        task(None, **kwargs)


def run_duty_cli(project: LifecycleProject, args: list[str]) -> int:
    """Forward raw arguments to Duty's native CLI parser."""
    parser = get_parser()
    opts = parser.parse_args(args=args)
    remainder = opts.remainder

    if opts.completion:
        print(Path(duty_cli.__file__).parent.joinpath("completions.bash").read_text(encoding="utf-8"))
        return 0

    if opts.complete:
        words = project.collection.completion_candidates(remainder)
        words += sorted(
            opt for opt, action in parser._option_string_actions.items() if action.help != argparse.SUPPRESS
        )
        print(*words, sep="\n")
        return 0

    if opts.help is not None:
        print_help(parser, opts, project.collection)
        return 0

    if opts.list:
        print(textwrap.indent(project.collection.format_help(), prefix="  "))
        return 0

    try:
        arg_lists = split_args(remainder, project.collection.names())
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not arg_lists:
        print_help(parser, opts, project.collection)
        return 1

    global_opts = specified_options(
        opts,
        exclude={"duties_file", "list", "help", "remainder", "complete", "completion"},
    )
    try:
        commands = parse_commands(arg_lists, global_opts, project.collection)
    except TypeError as exc:
        print(f"> {exc}", file=sys.stderr)
        return 1

    for task, posargs, kwargs in commands:
        kwargs = _coerce_cli_kwargs(task, kwargs)
        try:
            task.run(*posargs, **kwargs)
        except DutyFailure as failure:
            return failure.code
    return 0


def _coerce_cli_kwargs(task: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    function = getattr(task, "function", None)
    if function is None:
        return kwargs

    parameters = signature(function).parameters
    coerced = dict(kwargs)
    for name, value in kwargs.items():
        parameter = parameters.get(name)
        if parameter is None:
            continue
        if _is_bool_parameter(parameter):
            coerced[name] = _coerce_bool(value)
    return coerced


def _is_bool_parameter(parameter: Parameter) -> bool:
    return parameter.annotation is bool or isinstance(parameter.default, bool)


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return value


def _load_collection(path: Path) -> tuple[ModuleType, Collection]:
    collection = Collection(str(path))
    try:
        collection.load()
    except Exception as exc:
        _exit_project_error(f"Failed to import {path}.", str(exc))

    module = sys.modules.get("duty.duties")
    if not isinstance(module, ModuleType):
        _exit_project_error(f"Failed to import {path}.", "Duty did not expose the loaded module.")
    return module, collection


def _load_metadata(module: ModuleType) -> dict[str, Any]:
    raw = getattr(module, "AGENTSEEK", None)
    if not isinstance(raw, dict):
        _exit_project_error(
            "Missing AGENTSEEK lifecycle metadata in duties.py.",
            'Add AGENTSEEK = {"version": 1} to the project lifecycle file.',
        )

    version = raw.get("version")
    if version != SUPPORTED_LIFECYCLE_VERSION:
        _exit_project_error(
            f"Unsupported AgentSeek lifecycle version: {version!r}.",
            f"This AgentSeek release supports version {SUPPORTED_LIFECYCLE_VERSION}.",
        )
    return raw


def _validate_tasks(collection: Collection) -> None:
    task_names = set(collection.names())
    missing = [name for name in REQUIRED_TASKS if name not in task_names]
    if missing:
        _exit_project_error(
            f"Incomplete AgentSeek lifecycle: missing task(s): {', '.join(missing)}.",
            f"{LIFECYCLE_FILE} must expose dev, info, and doctor tasks.",
        )


def _exit_project_error(summary: str, detail: str) -> None:
    typer.echo(summary, err=True)
    typer.echo(detail, err=True)
    raise typer.Exit(2)


__all__ = [
    "LIFECYCLE_FILE",
    "REQUIRED_TASKS",
    "SUPPORTED_LIFECYCLE_VERSION",
    "LifecycleProject",
    "load_lifecycle_project",
    "run_duty_cli",
    "run_lifecycle_task",
]
