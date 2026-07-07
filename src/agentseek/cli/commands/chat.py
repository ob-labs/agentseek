"""Agent mode interactive chat session."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer


def chat(
    ctx: typer.Context,
    chat_id: Annotated[str, typer.Option("--chat-id", help="Chat id")] = "local",
    session_id: Annotated[str | None, typer.Option("--session-id", help="Optional session id")] = None,
) -> None:
    """Start an interactive CLI chat session."""
    from bub.channels.cli import CliChannel
    from bub.channels.manager import ChannelManager
    from bub.framework import BubFramework

    framework = ctx.ensure_object(BubFramework)
    manager = ChannelManager(
        framework,
        enabled_channels=["cli"],
        stream_output=True,
    )
    channel = manager.get_channel("cli")
    if not isinstance(channel, CliChannel):
        typer.echo("CLI channel not found. Please check your hook implementations.")
        raise typer.Exit(1)
    channel.set_metadata(chat_id=chat_id, session_id=session_id)
    asyncio.run(manager.listen_and_run())
