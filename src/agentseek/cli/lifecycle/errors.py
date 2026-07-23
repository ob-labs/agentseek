"""Lifecycle CLI error helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, NoReturn

import typer


class LifecycleInputError(Exception):
    """Base class for non-emitting authored lifecycle input errors."""

    code: ClassVar[str]


@dataclass(frozen=True)
class LifecycleNotFoundError(LifecycleInputError):
    """No lifecycle file was found while discovering a project."""

    legacy_detail: str
    code: ClassVar[str] = "lifecycle_not_found"


@dataclass(frozen=True)
class LifecycleTomlError(LifecycleInputError):
    """The lifecycle file could not be decoded as TOML."""

    line: int | None
    column: int | None
    legacy_detail: str
    code: ClassVar[str] = "lifecycle_toml_invalid"


@dataclass(frozen=True)
class LifecycleValidationIssue:
    """A redacted, application-owned lifecycle validation issue."""

    path: str
    code: str
    message: str


@dataclass(frozen=True)
class LifecycleValidationError(LifecycleInputError):
    """Lifecycle fields failed authored-spec validation."""

    lifecycle_version: int | None
    issues: tuple[LifecycleValidationIssue, ...]
    legacy_detail: str
    code: ClassVar[str] = "lifecycle_validation_failed"


@dataclass(frozen=True)
class LifecycleVersionUnsupportedError(LifecycleInputError):
    """The authored lifecycle version is not supported."""

    found: int | None
    supported: tuple[int, ...]
    legacy_detail: str
    code: ClassVar[str] = "lifecycle_version_unsupported"


def exit_project_error(summary: str, detail: str) -> NoReturn:
    """Print a project-scoped lifecycle error and exit with Typer usage code."""
    typer.echo(summary, err=True)
    typer.echo(detail, err=True)
    raise typer.Exit(2)


__all__ = [
    "LifecycleInputError",
    "LifecycleNotFoundError",
    "LifecycleTomlError",
    "LifecycleValidationError",
    "LifecycleValidationIssue",
    "LifecycleVersionUnsupportedError",
    "exit_project_error",
]
