"""``agentseek task`` — run project lifecycle spec tasks."""

from __future__ import annotations

import typer

from agentseek.cli.lifecycle import LIFECYCLE_SPEC_FILE, lifecycle_spec_exists, load_lifecycle_project, run_task_cli


def _is_help_request(args: list[str]) -> bool:
    return bool(args) and args[0] in {"--help", "-h"}


def _print_task_help() -> None:
    typer.echo("Usage: agentseek task [TASK]")
    typer.echo()
    typer.echo("Run project-defined lifecycle spec tasks.")
    typer.echo()
    typer.echo("Forms:")
    typer.echo("  agentseek task --list")
    typer.echo("  agentseek task <name>")
    typer.echo()
    typer.echo(f"This command must be run from a project containing {LIFECYCLE_SPEC_FILE}.")


def task(ctx: typer.Context) -> None:
    """Run lifecycle spec tasks from the current project."""
    args = list(ctx.args)
    if _is_help_request(args) and not lifecycle_spec_exists():
        _print_task_help()
        return
    project = load_lifecycle_project()
    code = run_task_cli(project, args)
    if code:
        raise typer.Exit(code)


__all__ = ["task"]
