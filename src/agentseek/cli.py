"""agentseek overrides for Bub's builtin CLI (onboard branding, install sandbox, …)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

import typer

from agentseek.env import DEFAULT_PLUGIN_SANDBOX

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


def agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


def _brand_onboard_echo(original_echo):
    def echo(message=None, *args, **kwargs):
        if message == "\nWelcome to Bub! Let's get you set up.\n":
            message = AGENTSEEK_ONBOARD_WELCOME
        return original_echo(message, *args, **kwargs)

    return echo


def resolve_enabled_channels(framework, primary_channels: Iterable[str]) -> list[str]:
    """Enable requested channels plus all lifecycle channels exposed by the framework."""
    enabled = list(dict.fromkeys(primary_channels))
    for channel_name in framework.get_channels(lambda _message: None):
        if channel_name.endswith(".lifecycle") and channel_name not in enabled:
            enabled.append(channel_name)
    return enabled


def apply_agentseek_onboard_branding() -> None:
    """Replace Bub's onboard banner and copy without changing the onboard workflow."""
    from bub.builtin import cli

    cli.ONBOARD_BANNER = AGENTSEEK_ONBOARD_BANNER
    cli.typer.echo = _brand_onboard_echo(cli.typer.echo)
    cli.__version__ = agentseek_version()


def apply_agentseek_chat_channel_defaults() -> None:
    """Include lifecycle channels in chat mode so MCP and similar helpers can boot."""
    import bub.builtin.cli as bub_cli
    from bub.channels.cli import CliChannel
    from bub.channels.manager import ChannelManager
    from bub.framework import BubFramework

    def chat(
        ctx: typer.Context,
        chat_id: str = bub_cli.typer.Option("local", "--chat-id", help="Chat id"),
        session_id: str | None = bub_cli.typer.Option(None, "--session-id", help="Optional session id"),
    ) -> None:
        framework = ctx.ensure_object(BubFramework)
        manager = ChannelManager(
            framework,
            enabled_channels=resolve_enabled_channels(framework, ["cli"]),
            stream_output=True,
        )
        channel = manager.get_channel("cli")
        if not isinstance(channel, CliChannel):
            bub_cli.typer.echo("CLI channel not found. Please check your hook implementations.")
            raise bub_cli.typer.Exit(1)
        channel.set_metadata(chat_id=chat_id, session_id=session_id)
        asyncio.run(manager.listen_and_run())

    object.__setattr__(bub_cli, "chat", chat)


def apply_agentseek_install_project_defaults() -> None:
    """Use :data:`~agentseek.env.DEFAULT_PLUGIN_SANDBOX` for Bub's plugin-install sandbox.

    Bub defaults to ``uv init --name bub-project``. agentseek aligns ``uv init --name`` with the
    default ``BUB_PROJECT`` path from :func:`~agentseek.env.apply_agentseek_env_aliases`.
    """
    import bub.builtin.cli as bub_cli

    def _ensure_plugin_sandbox(project: Path) -> None:
        if (project / "pyproject.toml").is_file():
            return
        bub_cli._uv("init", "--bare", "--name", DEFAULT_PLUGIN_SANDBOX, "--app", cwd=project)
        bub_requirement = bub_cli._build_bub_requirement()
        bub_cli._uv("add", "--active", "--no-sync", *bub_requirement, cwd=project)

    # Ruff B010 rewrites `setattr(mod, "const", ...)` to assignment; that breaks ty's monkeypatch
    # typing. ``object.__setattr__`` keeps dynamic binding and satisfies both.
    object.__setattr__(bub_cli, "_ensure_project", _ensure_plugin_sandbox)


def apply_agentseek_cli_overrides() -> None:
    """Patch ``bub.builtin.cli`` before ``BubFramework.create_cli_app`` registers commands.

    Apply onboarding branding first, then chat channel defaults and install sandbox behavior; all
    target the same module and must run before Typer binds builtin commands.
    """
    apply_agentseek_onboard_branding()
    apply_agentseek_chat_channel_defaults()
    apply_agentseek_install_project_defaults()


__all__ = [
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "agentseek_version",
    "apply_agentseek_chat_channel_defaults",
    "apply_agentseek_cli_overrides",
    "apply_agentseek_install_project_defaults",
    "apply_agentseek_onboard_branding",
    "resolve_enabled_channels",
]
