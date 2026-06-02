"""agentseek overrides for Bub's builtin CLI (onboard branding, install sandbox, …)."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Iterable
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from agentseek.env import DEFAULT_PLUGIN_SANDBOX

if TYPE_CHECKING:
    from bub.channels.cli import CliChannel
    from bub.channels.cli.renderer import CliRenderer
    from bub.channels.message import MessageKind
    from rich.live import Live

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


def _install_single_cli_log_sink(self: CliChannel) -> int:
    from loguru import logger

    with contextlib.suppress(ValueError):
        logger.remove()
    return logger.add(self._renderer.log, colorize=False, format="{level:<8} | {message}")


def _finish_cli_stream_once(self: CliRenderer, live: Live, *, kind: MessageKind, text: str) -> None:
    del self
    del kind, text
    live.stop()


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
    from bub.channels.cli.renderer import CliRenderer
    from bub.channels.manager import ChannelManager
    from bub.framework import BubFramework

    type.__setattr__(CliChannel, "_install_log_sink", _install_single_cli_log_sink)
    type.__setattr__(CliRenderer, "finish_stream", _finish_cli_stream_once)

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
        # Bub's own ``_default_project`` factory mkdir's the sandbox before
        # returning the path. When ``BUB_PROJECT`` is supplied through the
        # environment (which is what ``apply_agentseek_env_aliases`` does for
        # ``.agentseek/agentseek-project``), that factory is bypassed and the
        # directory may not exist yet — ``_uv(... cwd=project)`` would then
        # raise ``FileNotFoundError`` from ``subprocess.run``. Mirror Bub's
        # invariant here so ``agentseek install`` works in a fresh workspace.
        project.mkdir(parents=True, exist_ok=True)
        if (project / "pyproject.toml").is_file():
            return
        bub_cli._uv("init", "--bare", "--name", DEFAULT_PLUGIN_SANDBOX, "--app", cwd=project)
        bub_requirement = bub_cli._build_bub_requirement()
        bub_cli._uv("add", "--active", "--no-sync", *bub_requirement, cwd=project)

    # Ruff B010 rewrites `setattr(mod, "const", ...)` to assignment; that breaks ty's monkeypatch
    # typing. ``object.__setattr__`` keeps dynamic binding and satisfies both.
    object.__setattr__(bub_cli, "_ensure_project", _ensure_plugin_sandbox)


def apply_agentseek_install_requirement_resolution() -> None:
    """Route ``agentseek-*`` packages directly as bare names.

    Resolution order for bare names (no ``/``, no URL prefix):

    1. Name starts with ``agentseek-`` → pass bare name (uv resolves from workspace or PyPI).
    2. Otherwise → Bub's original ``_build_requirement`` (PyPI or bub-contrib).
    """
    import bub.builtin.cli as bub_cli

    _original_build_requirement = bub_cli._build_requirement

    def _build_requirement(spec: str) -> str:
        if spec.startswith(("git@", "https://")) or "/" in spec:
            return _original_build_requirement(spec)
        name, _, _ = spec.partition("@")
        if name.startswith("agentseek-"):
            return name
        return _original_build_requirement(spec)

    object.__setattr__(bub_cli, "_build_requirement", _build_requirement)


def apply_agentseek_cli_overrides() -> None:
    """Patch ``bub.builtin.cli`` before ``BubFramework.create_cli_app`` registers commands.

    Apply onboarding branding first, then chat channel defaults and install sandbox behavior; all
    target the same module and must run before Typer binds builtin commands.
    """
    apply_agentseek_onboard_branding()
    apply_agentseek_chat_channel_defaults()
    apply_agentseek_install_project_defaults()
    apply_agentseek_install_requirement_resolution()


__all__ = [
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "agentseek_version",
    "apply_agentseek_chat_channel_defaults",
    "apply_agentseek_cli_overrides",
    "apply_agentseek_install_project_defaults",
    "apply_agentseek_install_requirement_resolution",
    "apply_agentseek_onboard_branding",
    "resolve_enabled_channels",
]
