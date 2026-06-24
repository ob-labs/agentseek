"""``agentseek doctor`` — diagnose local project readiness."""

from __future__ import annotations

from typing import Annotated

import typer

from agentseek.cli.lifecycle import load_lifecycle_project, run_lifecycle_task

app = typer.Typer(
    name="doctor",
    help="Check local project readiness through the lifecycle spec.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def doctor(
    live: Annotated[
        bool,
        typer.Option("--live", help="Check already-running local services."),
    ] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Return non-zero when warnings are present."),
    ] = False,
) -> None:
    """Run static and optional live checks for the current project."""
    project = load_lifecycle_project()
    run_lifecycle_task(project, "doctor", live=live, strict=strict)


__all__ = ["app"]
