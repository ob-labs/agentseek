"""Safety primitives for authored lifecycle values."""

from __future__ import annotations

import ntpath
import re
from pathlib import Path

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_BARE_EXECUTABLE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


class UnsafeProjectPathError(ValueError):
    """A project-relative path failed lexical or resolved confinement."""

    def __init__(self) -> None:
        super().__init__("project path is unsafe")


def validate_identifier(value: str) -> str:
    """Return a lifecycle identifier after enforcing its safe grammar."""
    if _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError
    return value


def validate_bare_executable(value: str) -> str:
    """Return a bare executable name after enforcing its safe grammar."""
    if value in {".", ".."} or _BARE_EXECUTABLE_PATTERN.fullmatch(value) is None:
        raise ValueError
    return value


def resolve_confined_project_path(project_root: Path, value: str, *, allow_dot: bool = False) -> Path:
    """Resolve a project-relative path only when it remains confined to the root."""
    if _path_is_lexically_unsafe(value, allow_dot=allow_dot):
        raise UnsafeProjectPathError()

    try:
        root = project_root.resolve(strict=False)
        candidate = (root / value).resolve(strict=False)
        candidate.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise UnsafeProjectPathError() from None
    return candidate


def _path_is_lexically_unsafe(value: str, *, allow_dot: bool) -> bool:
    if not value.strip() or "\x00" in value:
        return True
    if Path(value).is_absolute() or ntpath.isabs(value) or ntpath.splitdrive(value)[0]:
        return True
    segments = re.split(r"[/\\]", value)
    if all(segment in {"", "."} for segment in segments):
        return not allow_dot
    return ".." in segments


__all__ = [
    "UnsafeProjectPathError",
    "resolve_confined_project_path",
    "validate_bare_executable",
    "validate_identifier",
]
