"""``agentseek chat`` — interactive CLI chat session with lifecycle channels."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

import typer


def resolve_enabled_channels(framework, primary_channels: Iterable[str]) -> list[str]:
    """Enable requested channels plus Bub support channels exposed as ``*.lifecycle``."""
    enabled = list(dict.fromkeys(primary_channels))
    for channel_name in framework.get_channels(lambda _message: None):
        if channel_name.endswith(".lifecycle") and channel_name not in enabled:
            enabled.append(channel_name)
    return enabled


def chat(
    ctx: typer.Context,
    chat_id: str = typer.Option("local", "--chat-id", help="Chat id"),
    session_id: str | None = typer.Option(None, "--session-id", help="Optional session id"),
) -> None:
    """Start an interactive CLI chat session."""
    from bub.channels.cli import CliChannel
    from bub.channels.manager import ChannelManager
    from bub.framework import BubFramework

    framework = ctx.ensure_object(BubFramework)
    manager = ChannelManager(
        framework,
        enabled_channels=resolve_enabled_channels(framework, ["cli"]),
        stream_output=True,
    )
    channel = manager.get_channel("cli")
    if not isinstance(channel, CliChannel):
        typer.echo("CLI channel not found. Please check your hook implementations.")
        raise typer.Exit(1)
    channel.set_metadata(chat_id=chat_id, session_id=session_id)
    asyncio.run(manager.listen_and_run())
