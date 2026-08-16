"""``agentseek dev`` — run a generated project through its lifecycle spec."""

from __future__ import annotations

from typing import Annotated

import typer

from agentseek.cli.lifecycle import (
    LifecycleDotenvError,
    load_lifecycle_project,
    resolve_project_environment,
    run_lifecycle_task,
)
from agentseek.cli.lifecycle.errors import exit_project_error

app = typer.Typer(
    name="dev",
    help="Run the current project locally through the lifecycle spec.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def dev(
    skip_check: Annotated[
        bool,
        typer.Option("--skip-check", help="Skip the preliminary strict doctor pass before running dev."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the startup plan without launching services."),
    ] = False,
) -> None:
    """Run the local app defined by the lifecycle spec."""
    project = load_lifecycle_project()
    if dry_run:
        run_lifecycle_task(project, "dev", dry_run=True)
        return

    try:
        environment = resolve_project_environment(project)
    except LifecycleDotenvError as exc:
        exit_project_error("Invalid lifecycle environment.", str(exc))
    if not skip_check:
        run_lifecycle_task(project, "doctor", strict=True, environment=environment)
    run_lifecycle_task(project, "dev", dry_run=False, environment=environment)


__all__ = ["app"]
