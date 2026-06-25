from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable
from pathlib import Path

import typer
from bub.channels.base import Channel
from bub.channels.message import ChannelMessage
from bub.framework import BubFramework
from republic import StreamEvent
from typer.testing import CliRunner

from agentseek.cli import apply_agentseek_runtime_command_layout, resolve_enabled_channels
from agentseek.cli.commands.chat import chat as agentseek_chat
from agentseek.cli.commands.onboard import onboard as agentseek_onboard
from agentseek.cli.commands.plugin import _ensure_plugin_sandbox
from agentseek.env import DEFAULT_PLUGIN_SANDBOX
from tests.cli_commands.helpers import build_command_app


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


def test_runtime_command_layout_replaces_and_regroups_bub_commands() -> None:
    app = typer.Typer()

    @app.command("run")
    def run() -> None:
        pass

    @app.command("install")
    def install() -> None:
        pass

    @app.command("uninstall")
    def uninstall() -> None:
        pass

    @app.command("update")
    def update() -> None:
        pass

    @app.command("chat")
    def chat() -> None:
        pass

    @app.command("onboard")
    def onboard() -> None:
        pass

    apply_agentseek_runtime_command_layout(app)

    root_commands = {command.name for command in app.registered_commands}
    assert app.suggest_commands is False
    # Bub originals removed from root
    assert "run" not in root_commands
    assert "install" not in root_commands
    assert "uninstall" not in root_commands
    assert "update" not in root_commands
    # AgentSeek replacements present
    assert "turn" in root_commands
    assert "chat" in root_commands
    assert "onboard" in root_commands

    # chat and onboard are AgentSeek's own implementations
    chat_cmd = next(c for c in app.registered_commands if c.name == "chat")
    assert chat_cmd.callback is agentseek_chat
    onboard_cmd = next(c for c in app.registered_commands if c.name == "onboard")
    assert onboard_cmd.callback is agentseek_onboard

    # plugin group
    plugin_groups = [group.typer_instance for group in app.registered_groups if group.name == "plugin"]
    assert len(plugin_groups) == 1
    assert plugin_groups[0] is not None
    assert {command.name for command in plugin_groups[0].registered_commands} == {
        "install",
        "list",
        "uninstall",
        "update",
    }


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


# ---------------------------------------------------------------------------
# Plugin sandbox
# ---------------------------------------------------------------------------


def test_ensure_plugin_sandbox_calls_uv_init_with_agentseek_name(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    monkeypatch.setattr(bub_cli, "_build_bub_requirement", lambda: ["bub"])

    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    _ensure_plugin_sandbox(sandbox)

    init_line = next(row for row in captured if row[:2] == ["init", "--bare"])
    assert "--name" in init_line
    assert init_line[init_line.index("--name") + 1] == DEFAULT_PLUGIN_SANDBOX
    add_line = next(row for row in captured if row and row[0] == "add")
    assert add_line[:3] == ["add", "--active", "--no-sync"]
    assert "bub" in add_line


def test_ensure_plugin_sandbox_skips_uv_when_pyproject_exists(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")

    _ensure_plugin_sandbox(tmp_path)

    assert captured == []


def test_ensure_plugin_sandbox_creates_directory_when_missing(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    cwds: list[Path] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        if not cwd.is_dir():
            raise FileNotFoundError(cwd)
        cwds.append(cwd)

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    monkeypatch.setattr(bub_cli, "_build_bub_requirement", lambda: ["bub"])

    sandbox = tmp_path / "missing-sandbox"
    assert not sandbox.exists()

    _ensure_plugin_sandbox(sandbox)

    assert sandbox.is_dir()
    assert cwds == [sandbox, sandbox]


def test_plugin_list_reports_missing_sandbox_without_mutation(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    calls: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        calls.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)

    sandbox = tmp_path / "missing-sandbox"
    result = CliRunner().invoke(build_command_app(), ["plugin", "list", "--project", str(sandbox)])

    assert result.exit_code == 0, result.output
    assert f"Plugin project: {sandbox.resolve()}" in result.output
    assert "Plugin sandbox not found." in result.output
    assert not sandbox.exists()
    assert calls == []


def test_plugin_list_reports_empty_sandbox_without_uv(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    calls: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        calls.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "agentseek-plugins"\ndependencies = ["requests>=2"]\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(build_command_app(), ["plugin", "list", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert f"Plugin project: {tmp_path.resolve()}" in result.output
    assert "No AgentSeek/Bub plugin packages found." in result.output
    assert "requests" not in result.output
    assert calls == []


def test_plugin_list_prints_agentseek_and_bub_dependencies_without_uv(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    calls: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        calls.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    (tmp_path / "pyproject.toml").write_text(
        "\n".join([
            "[project]",
            'name = "agentseek-plugins"',
            "dependencies = [",
            '  "bub==0.3.9",',
            '  "agentseek-langchain>=0.1",',
            '  "bub-mcp",',
            '  "requests>=2",',
            "]",
            "",
        ]),
        encoding="utf-8",
    )

    result = CliRunner().invoke(build_command_app(), ["plugin", "list", "--project", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert f"Plugin project: {tmp_path.resolve()}" in result.output
    assert "Installed plugin packages:" in result.output
    assert "bub==0.3.9" in result.output
    assert "agentseek-langchain>=0.1" in result.output
    assert "bub-mcp" in result.output
    assert "requests" not in result.output
    assert calls == []
