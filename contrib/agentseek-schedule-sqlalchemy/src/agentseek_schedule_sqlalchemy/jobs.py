from __future__ import annotations

import asyncio
from pathlib import Path

from bub import BubFramework
from bub.channels.message import ChannelMessage

SCHEDULE_SUBPROCESS_TIMEOUT_SECONDS = 300


def _noop() -> None:
    """No-op for tests (must be module-level for pickle ref)."""
    pass


def _build_message(message: str, session_id: str) -> ChannelMessage:
    if ":" in session_id:
        channel, chat_id = session_id.split(":", 1)
    else:
        channel = "schedule"
        chat_id = "default"
    return ChannelMessage(
        content=message,
        session_id=session_id,
        channel=channel,
        chat_id=chat_id,
    )


async def _run_with_fresh_framework(payload: ChannelMessage, workspace: str | None = None) -> None:
    framework = BubFramework()
    framework.load_hooks()
    if workspace:
        framework.workspace = Path(workspace).resolve()
    await framework.process_inbound(payload)


async def run_scheduled_reminder_async(message: str, session_id: str, workspace: str | None = None) -> None:
    from agentseek_schedule_sqlalchemy.channel import ScheduleChannel

    payload = _build_message(message, session_id)
    try:
        await ScheduleChannel.dispatch_message(payload)
    except RuntimeError:
        await _run_with_fresh_framework(payload, workspace)


def run_scheduled_reminder(message: str, session_id: str, workspace: str | None = None) -> None:
    """Synchronous job target for BackgroundScheduler (runs in a worker thread).

    APScheduler's BackgroundScheduler executes jobs in a thread pool; ``async def`` targets are
    not supported with the default executor. Each run uses ``asyncio.run()`` with a fresh loop.
    """
    from agentseek_schedule_sqlalchemy.channel import ScheduleChannel

    payload = _build_message(message, session_id)
    try:
        ScheduleChannel.dispatch_message_sync(payload)
    except RuntimeError:
        asyncio.run(_run_with_fresh_framework(payload, workspace))
