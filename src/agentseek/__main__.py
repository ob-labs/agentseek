from __future__ import annotations

import importlib
import sys

import typer

from agentseek.cli import apply_agentseek_cli_overrides
from agentseek.env import (
    agentseek_config_file,
    apply_agentseek_env_aliases,
    get_observability_settings,
)

apply_agentseek_env_aliases()
apply_agentseek_cli_overrides()


def _maybe_enable_observability() -> None:
    try:
        observability = importlib.import_module("agentseek_observability.plugin")
    except ModuleNotFoundError:
        return

    instrument = getattr(observability, "instrument_agentseek_observability", None)
    if callable(instrument):
        instrument()


def _instrument_agentseek() -> None:
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, colorize=True)

    try:
        logfire = importlib.import_module("logfire")
        logfire_loguru = importlib.import_module("logfire.integrations.loguru")
    except ModuleNotFoundError:
        return

    # Default to local-only spans. Opt into the hosted Logfire backend by
    # exporting ``AGENTSEEK_SEND_TO_LOGFIRE=true`` (see
    # ``AgentseekObservabilitySettings``).
    settings = get_observability_settings()
    logfire.configure(send_to_logfire=settings.send_to_logfire)
    logger.add(logfire_loguru.LogfireHandler(), format="{message}")
    _maybe_enable_observability()


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
