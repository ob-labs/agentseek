from __future__ import annotations

import importlib
import sys

import typer

from agentseek.branding import apply_agentseek_onboard_branding
from agentseek.env import agentseek_config_file, apply_agentseek_env_aliases

apply_agentseek_env_aliases()
apply_agentseek_onboard_branding()


def _instrument_agentseek() -> None:
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, colorize=True)

    try:
        logfire = importlib.import_module("logfire")
    except ModuleNotFoundError:
        pass
    else:
        logfire.configure()
        logger.add(logfire.loguru_handler())


def create_cli_app() -> typer.Typer:
    from bub.framework import BubFramework

    _instrument_agentseek()
    framework = BubFramework(config_file=agentseek_config_file())
    framework.load_hooks()
    app = framework.create_cli_app()

    if not app.registered_commands:

        @app.command("help")
        def _help() -> None:
            typer.echo("No CLI command loaded.")

    return app


app = create_cli_app()

__all__ = ["app", "create_cli_app"]


if __name__ == "__main__":
    app()
