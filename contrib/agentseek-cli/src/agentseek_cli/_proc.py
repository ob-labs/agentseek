"""Subprocess helpers for shelling out to external CLIs via ``uvx``."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

import typer


def find_uvx() -> str:
    """Return the resolved ``uvx`` executable path or raise a friendly Typer error."""
    path = shutil.which("uvx")
    if path is None:
        _raise_missing_uvx()
    return path


def run_uvx(
    distribution: str,
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    from_spec: str | None = None,
) -> int:
    """Invoke ``uvx [--from <spec>] <distribution> [...argv]`` and return its exit code.

    ``from_spec`` lets callers pin a version or point at a local wheel/git ref
    while keeping the invoked entry-point name (``distribution``) stable.
    """
    uvx = find_uvx()
    command: list[str] = [uvx]
    if from_spec is not None:
        command.extend(["--from", from_spec])
    command.append(distribution)
    command.extend(argv)
    completed = subprocess.run(command, cwd=str(cwd) if cwd is not None else None, check=False)  # noqa: S603
    return completed.returncode


def _raise_missing_uvx() -> NoReturn:
    typer.echo(
        "`uvx` was not found on PATH. AgentSeek CLI uses uvx to invoke "
        "external tools such as `npx-skills`.\n"
        "Install uv (which ships uvx) from https://docs.astral.sh/uv/ and retry.",
        err=True,
    )
    raise typer.Exit(1)


__all__ = ["find_uvx", "run_uvx"]
