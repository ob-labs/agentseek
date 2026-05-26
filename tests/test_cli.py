from __future__ import annotations

import asyncio
import importlib
from collections.abc import AsyncIterable
from pathlib import Path

import typer
from bub.channels.base import Channel
from bub.channels.message import ChannelMessage
from bub.framework import BubFramework
from click import Command
from republic import StreamEvent
from rich.console import Console
from typer.testing import CliRunner

from agentseek.cli import (
    AGENTSEEK_ONBOARD_BANNER,
    AGENTSEEK_ONBOARD_WELCOME,
    _finish_cli_stream_once,
    _install_single_cli_log_sink,
    agentseek_version,
    apply_agentseek_chat_channel_defaults,
    apply_agentseek_cli_overrides,
    apply_agentseek_install_project_defaults,
    apply_agentseek_onboard_branding,
    resolve_enabled_channels,
)
from agentseek.env import DEFAULT_PLUGIN_SANDBOX

runner = CliRunner()


class _DummyChannel(Channel):
    name = "dummy"

    async def start(self, stop_event: asyncio.Event) -> None:
        del stop_event

    async def stop(self) -> None:
        return

    def stream_events(self, message: ChannelMessage, stream: AsyncIterable[StreamEvent]) -> AsyncIterable[StreamEvent]:
        del message
        return stream


def test_agentseek_onboard_branding_replaces_bub_banner(monkeypatch) -> None:
    from bub.builtin import cli

    importlib.reload(cli)

    messages = []

    def echo(message=None, *args, **kwargs):
        del args, kwargs
        messages.append(message)

    monkeypatch.setattr(cli, "ONBOARD_BANNER", "Bub v{version}")
    monkeypatch.setattr(cli, "__version__", "bub-version")
    monkeypatch.setattr(cli.typer, "echo", echo)

    apply_agentseek_onboard_branding()

    rendered = cli.ONBOARD_BANNER.format(version=cli.__version__)
    cli.typer.echo("\nWelcome to Bub! Let's get you set up.\n")
    cli.typer.echo("unchanged")

    assert cli.ONBOARD_BANNER == AGENTSEEK_ONBOARD_BANNER
    assert cli.__version__ == agentseek_version()
    assert "AGENTSEEK" in rendered
    assert agentseek_version() in rendered
    assert messages == [AGENTSEEK_ONBOARD_WELCOME, "unchanged"]


def test_apply_agentseek_cli_overrides_runs_onboard_then_install(monkeypatch) -> None:
    order: list[str] = []

    def fake_onboard() -> None:
        order.append("onboard")

    def fake_chat() -> None:
        order.append("chat")

    def fake_install() -> None:
        order.append("install")

    monkeypatch.setattr("agentseek.cli.apply_agentseek_onboard_branding", fake_onboard)
    monkeypatch.setattr("agentseek.cli.apply_agentseek_chat_channel_defaults", fake_chat)
    monkeypatch.setattr("agentseek.cli.apply_agentseek_install_project_defaults", fake_install)

    apply_agentseek_cli_overrides()

    assert order == ["onboard", "chat", "install"]


class _FakeFramework(BubFramework):
    def __init__(self) -> None:
        pass

    def get_channels(self, message_handler) -> dict[str, Channel]:
        del message_handler
        return {
            "cli": _DummyChannel(),
            "mcp.lifecycle": _DummyChannel(),
            "skills.lifecycle": _DummyChannel(),
            "telegram": _DummyChannel(),
        }


def test_resolve_enabled_channels_adds_lifecycle_channels() -> None:
    enabled = resolve_enabled_channels(_FakeFramework(), ["cli"])

    assert enabled == ["cli", "mcp.lifecycle", "skills.lifecycle"]


def test_resolve_enabled_channels_preserves_explicit_entries() -> None:
    enabled = resolve_enabled_channels(_FakeFramework(), ["cli", "mcp.lifecycle"])

    assert enabled == ["cli", "mcp.lifecycle", "skills.lifecycle"]


def test_apply_agentseek_chat_channel_defaults_enables_lifecycle_channels(monkeypatch) -> None:
    import asyncio

    import bub.builtin.cli as bub_cli
    import bub.channels.cli as cli_channel_module
    import bub.channels.manager as manager_module

    importlib.reload(bub_cli)

    captured: dict[str, object] = {}
    original = bub_cli.chat

    class FakeChannel:
        def __init__(self) -> None:
            self.metadata: dict[str, str | None] = {}

        def set_metadata(self, *, chat_id: str, session_id: str | None) -> None:
            self.metadata = {"chat_id": chat_id, "session_id": session_id}

    class FakeManager:
        def __init__(self, framework, *, enabled_channels, stream_output) -> None:
            del framework
            captured["enabled_channels"] = list(enabled_channels)
            captured["stream_output"] = stream_output
            self.channel = FakeChannel()
            captured["channel"] = self.channel

        def get_channel(self, name: str):
            captured["channel_name"] = name
            return self.channel

        async def listen_and_run(self) -> str:
            captured["listen_called"] = True
            return "ok"

    def fake_asyncio_run(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    monkeypatch.setattr(manager_module, "ChannelManager", FakeManager)
    monkeypatch.setattr(cli_channel_module, "CliChannel", FakeChannel)
    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)

    try:
        apply_agentseek_chat_channel_defaults()
        fake_ctx = typer.Context(Command("chat"), obj=_FakeFramework())
        bub_cli.chat(fake_ctx, chat_id="chat-1", session_id="session-1")
    finally:
        object.__setattr__(bub_cli, "chat", original)

    assert captured["enabled_channels"] == ["cli", "mcp.lifecycle", "skills.lifecycle"]
    assert captured["stream_output"] is True
    assert captured["channel_name"] == "cli"
    assert captured["listen_called"] is True
    channel = captured["channel"]
    assert isinstance(channel, FakeChannel)
    assert channel.metadata == {"chat_id": "chat-1", "session_id": "session-1"}


def test_install_single_cli_log_sink_replaces_existing_sinks(monkeypatch) -> None:
    import loguru
    from bub.channels.cli import CliChannel

    removed: list[tuple[tuple[object, ...], dict[str, object]]] = []
    added: list[tuple[object, dict[str, object]]] = []

    monkeypatch.setattr(loguru.logger, "remove", lambda *args, **kwargs: removed.append((args, kwargs)))
    monkeypatch.setattr(loguru.logger, "add", lambda sink, **kwargs: added.append((sink, kwargs)) or 7)

    channel = CliChannel.__new__(CliChannel)
    channel._renderer = type("Renderer", (), {"log": object()})()

    handler_id = _install_single_cli_log_sink(channel)

    assert handler_id == 7
    assert removed == [((), {})]
    assert added == [(channel._renderer.log, {"colorize": False, "format": "{level:<8} | {message}"})]


def test_finish_cli_stream_once_stops_without_extra_update() -> None:
    from bub.channels.cli.renderer import CliRenderer

    calls: list[str] = []

    class FakeLive:
        def stop(self) -> None:
            calls.append("stop")

        def update(self, *args, **kwargs) -> None:
            del args, kwargs
            calls.append("update")

    _finish_cli_stream_once(CliRenderer(Console()), FakeLive(), kind="normal", text="hello")

    assert calls == ["stop"]


def test_install_project_defaults_calls_uv_init_with_agentseek_sandbox_name(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    monkeypatch.setattr(bub_cli, "_build_bub_requirement", lambda: ["bub"])

    original = bub_cli._ensure_project
    try:
        apply_agentseek_install_project_defaults()
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        bub_cli._ensure_project(sandbox)
    finally:
        object.__setattr__(bub_cli, "_ensure_project", original)

    init_line = next(row for row in captured if row[:2] == ["init", "--bare"])
    assert "--name" in init_line
    assert init_line[init_line.index("--name") + 1] == DEFAULT_PLUGIN_SANDBOX
    add_line = next(row for row in captured if row and row[0] == "add")
    assert add_line[:3] == ["add", "--active", "--no-sync"]
    assert "bub" in add_line


def test_install_project_defaults_skips_uv_when_pyproject_exists(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")

    original = bub_cli._ensure_project
    try:
        apply_agentseek_install_project_defaults()
        bub_cli._ensure_project(tmp_path)
    finally:
        object.__setattr__(bub_cli, "_ensure_project", original)

    assert captured == []


def test_install_project_defaults_creates_sandbox_when_missing(monkeypatch, tmp_path) -> None:
    """``BUB_PROJECT`` may point at a path that does not exist yet (the default
    ``.agentseek/agentseek-project`` sandbox). The override must mkdir before
    invoking ``uv``, otherwise ``subprocess.run`` raises ``FileNotFoundError``.
    """
    import bub.builtin.cli as bub_cli

    cwds: list[Path] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        # If the override forgot to mkdir, this would mirror the real
        # subprocess failure.
        if not cwd.is_dir():
            raise FileNotFoundError(cwd)
        cwds.append(cwd)

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    monkeypatch.setattr(bub_cli, "_build_bub_requirement", lambda: ["bub"])

    sandbox = tmp_path / "missing-sandbox"
    assert not sandbox.exists()

    original = bub_cli._ensure_project
    try:
        apply_agentseek_install_project_defaults()
        bub_cli._ensure_project(sandbox)
    finally:
        object.__setattr__(bub_cli, "_ensure_project", original)

    assert sandbox.is_dir()
    assert cwds == [sandbox, sandbox]
