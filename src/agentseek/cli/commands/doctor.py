"""``agentseek doctor`` — diagnose local project readiness."""

from __future__ import annotations

from typing import Annotated

import typer

from agentseek.cli.lifecycle import load_lifecycle_project, run_lifecycle_task
from agentseek.cli.lifecycle.json_commands import print_doctor_json

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
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit versioned machine-readable diagnostic results."),
    ] = False,
) -> None:
    """Run static and optional live checks for the current project."""
    if json_output:
        print_doctor_json(live=live, strict=strict)
        return
    project = load_lifecycle_project()
    run_lifecycle_task(project, "doctor", live=live, strict=strict)


__all__ = ["app"]
