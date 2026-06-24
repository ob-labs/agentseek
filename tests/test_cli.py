from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterable

import typer
from bub.channels.base import Channel
from bub.channels.message import ChannelMessage
from bub.framework import BubFramework
from republic import StreamEvent
from typer.testing import CliRunner

from agentseek.cli import (
    apply_agentseek_agent_command_layout,
    apply_agentseek_runtime_command_layout,
    register_app_profile_options,
)
from agentseek.cli.commands import chat as chat_module

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class _DummyChannel(Channel):
    name = "dummy"

    async def start(self, stop_event: asyncio.Event) -> None:
        del stop_event

    async def stop(self) -> None:
        return

    def stream_events(self, message: ChannelMessage, stream: AsyncIterable[StreamEvent]) -> AsyncIterable[StreamEvent]:
        del message
        return stream


# ---------------------------------------------------------------------------
# Command layout
# ---------------------------------------------------------------------------


def test_default_command_layout_mounts_lifecycle_commands() -> None:
    app = typer.Typer(name="agentseek", add_completion=False)
    register_app_profile_options(app)
    apply_agentseek_runtime_command_layout(app)

    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("create", "dev", "info", "doctor", "task"):
        assert command in result.output
    for removed_command in ("run", "build", "deploy", "gateway"):
        assert removed_command not in result.output


def test_removed_commands_are_not_registered() -> None:
    app = typer.Typer(name="agentseek", add_completion=False)
    register_app_profile_options(app)
    apply_agentseek_runtime_command_layout(app)

    runner = CliRunner()
    for command in ("run", "build", "deploy", "gateway"):
        result = runner.invoke(app, [command])
        assert result.exit_code == 2


def test_lifecycle_command_help_does_not_advertise_subcommands() -> None:
    app = typer.Typer(name="agentseek", add_completion=False)
    register_app_profile_options(app)
    apply_agentseek_runtime_command_layout(app)

    runner = CliRunner()
    for command in ("doctor", "dev", "info"):
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
        output = ANSI_RE.sub("", result.output)
        assert f"Usage: agentseek {command} [OPTIONS]" in output
        assert "COMMAND [ARGS]" not in output


def test_task_help_is_available_outside_lifecycle_project() -> None:
    app = typer.Typer(name="agentseek", add_completion=False)
    register_app_profile_options(app)
    apply_agentseek_runtime_command_layout(app)

    result = CliRunner().invoke(app, ["task", "--help"])

    assert result.exit_code == 0
    assert "Usage: agentseek task" in result.output
    assert ".agentseek/lifecycle.toml" in result.output


# ---------------------------------------------------------------------------
# Channel resolution
# ---------------------------------------------------------------------------


class _FakeFramework(BubFramework):
    def __init__(self) -> None:
        pass

    def get_channels(self, message_handler) -> dict[str, Channel]:
        del message_handler
        return {
            "cli": _DummyChannel(),
            "telegram": _DummyChannel(),
        }


def test_agent_command_layout_requires_confirmation(monkeypatch) -> None:
    app = typer.Typer(name="agentseek")
    framework = _FakeFramework()
    called = False

    def fake_chat(ctx: typer.Context) -> None:
        nonlocal called
        assert ctx.obj is framework
        called = True

    monkeypatch.setattr(chat_module, "chat", fake_chat)
    apply_agentseek_agent_command_layout(app, framework)

    result = CliRunner().invoke(app, ["--mode", "agent"], input="n\n")

    assert result.exit_code == 1
    assert called is False


def test_agent_command_layout_starts_chat_when_confirmed(monkeypatch) -> None:
    app = typer.Typer(name="agentseek")
    framework = _FakeFramework()
    called = False

    def fake_chat(ctx: typer.Context) -> None:
        nonlocal called
        assert ctx.obj is framework
        called = True

    monkeypatch.setattr(chat_module, "chat", fake_chat)
    apply_agentseek_agent_command_layout(app, framework)

    result = CliRunner().invoke(app, ["--mode", "agent"], input="y\n")

    assert result.exit_code == 0
    assert called is True
