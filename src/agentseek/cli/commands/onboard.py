"""``agentseek onboard`` — branded interactive configuration wizard."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

AGENTSEEK_ONBOARD_BANNER = r"""
    _                    _                 _
   / \   __ _  ___ _ __ | |_ ___  ___  ___| | __
  / _ \ / _` |/ _ \ '_ \| __/ __|/ _ \/ _ \ |/ /
 / ___ \ (_| |  __/ | | | |_\__ \  __/  __/   <
/_/   \_\__, |\___|_| |_|\__|___/\___|\___|_|\_\
        |___/
AGENTSEEK v{version}
""".strip("\n")
AGENTSEEK_ONBOARD_WELCOME = "\nWelcome to agentseek! Let's get you set up.\n"


def _agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


def onboard(ctx: typer.Context) -> None:
    """Interactively collect plugin configuration and write it to the AgentSeek config file."""
    from bub import configure
    from bub.framework import BubFramework

    framework = ctx.ensure_object(BubFramework)
    typer.echo(AGENTSEEK_ONBOARD_BANNER.format(version=_agentseek_version()))
    typer.echo(AGENTSEEK_ONBOARD_WELCOME)

    try:
        config_data = framework.collect_onboard_config()
        configure.save(framework.config_file, config_data)
    except (typer.Abort, typer.Exit):
        raise
    except Exception as exc:
        typer.secho(f"Onboarding failed: {exc}", err=True, fg="red")
        raise typer.Exit(1) from exc

    typer.echo(f"Saved config to {framework.config_file}")
