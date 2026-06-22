"""``agentseek dev`` — run a generated project through its lifecycle file."""

from __future__ import annotations

from typing import Annotated

import typer

from agentseek.cli.lifecycle import load_lifecycle_project, run_lifecycle_task

app = typer.Typer(
    name="dev",
    help="Run the current project locally through duties.py.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def dev(
    skip_check: Annotated[
        bool,
        typer.Option("--skip-check", help="Skip the strict readiness check before running dev."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the startup plan without launching services."),
    ] = False,
) -> None:
    """Run the local app defined by ``duties.py``."""
    project = load_lifecycle_project()
    if not skip_check and not dry_run:
        run_lifecycle_task(project, "doctor", strict=True)
    run_lifecycle_task(project, "dev", dry_run=dry_run)


__all__ = ["app"]
