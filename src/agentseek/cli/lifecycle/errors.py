"""Lifecycle CLI error helpers."""

from __future__ import annotations

from typing import NoReturn

import typer


def exit_project_error(summary: str, detail: str) -> NoReturn:
    """Print a project-scoped lifecycle error and exit with Typer usage code."""
    typer.echo(summary, err=True)
    typer.echo(detail, err=True)
    raise typer.Exit(2)


__all__ = ["exit_project_error"]
