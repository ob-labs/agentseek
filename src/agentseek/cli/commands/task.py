"""``agentseek task`` — forward project lifecycle duties."""

from __future__ import annotations

import typer

from agentseek.cli.lifecycle import load_lifecycle_project, run_duty_cli


def task(ctx: typer.Context) -> None:
    """Forward arbitrary duty commands from the current project."""
    project = load_lifecycle_project()
    code = run_duty_cli(project, list(ctx.args))
    if code:
        raise typer.Exit(code)


__all__ = ["task"]
