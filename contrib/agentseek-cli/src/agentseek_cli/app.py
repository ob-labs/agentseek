"""Single source of truth for the AgentSeek CLI surface.

``build_app()`` returns a fresh ``typer.Typer`` with every documented top-level
group attached. The standalone console script and the Bub plugin both go
through this function so the two entry shapes stay in sync.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

import typer

from agentseek_cli.commands import api, build, create, ctx, deploy, run, skills

CLI_HELP = "AgentSeek project-lifecycle CLI. Scaffold, run, build, deploy, manage API services, skills, and context."


def _get_version_string() -> str:
    import contextlib

    parts: list[str] = []
    try:
        parts.append(f"agentseek-cli {_pkg_version('agentseek-cli')}")
    except PackageNotFoundError:
        parts.append("agentseek-cli (unknown)")
    with contextlib.suppress(PackageNotFoundError):
        parts.append(f"agentseek {_pkg_version('agentseek')}")
    return "\n".join(parts)


COMMAND_PANELS: dict[str, str] = {
    "create": "Project",
    "run": "Project",
    "build": "Project",
    "deploy": "Project",
    "api": "Services",
    "ctx": "Services",
    "skills": "Services",
}


def iter_command_groups() -> tuple[typer.Typer, ...]:
    """Return the top-level Typer groups that make up the AgentSeek CLI.

    The order here is the order users see in ``agentseek --help``.
    """
    return (
        create.app,
        run.app,
        build.app,
        deploy.app,
        api.app,
        ctx.app,
        skills.app,
    )


def register_version_command(app: typer.Typer) -> None:
    """Add ``agentseek version`` to the given app."""

    @app.command("version", rich_help_panel="Environment")
    def version_cmd() -> None:
        """Show version information."""
        typer.echo(_get_version_string())


def build_app() -> typer.Typer:
    """Build a fresh standalone Typer app named ``agentseek``."""
    app = typer.Typer(
        name="agentseek",
        help=CLI_HELP,
        add_completion=False,
        no_args_is_help=True,
    )
    for sub in iter_command_groups():
        name = sub.info.name or ""
        panel = COMMAND_PANELS.get(name)
        app.add_typer(sub, name=name, rich_help_panel=panel)
    register_version_command(app)
    return app


__all__ = ["CLI_HELP", "build_app", "iter_command_groups", "register_version_command"]
