"""AgentSeek runtime layer — reimplements Bub builtin commands with AgentSeek branding and behavior.

Design: Bub's ``register_cli_commands`` hookspec uses ``call_many_sync`` (all
implementations execute, order not deterministic).  There is no built-in
override mechanism, so AgentSeek cannot reliably replace commands via hooks.

Instead, ``apply_agentseek_runtime_command_layout`` runs *after*
``BubFramework.create_cli_app()`` returns: it pops Bub's builtin commands and
re-registers AgentSeek's own implementations.  The reimplementations import
Bub's low-level utilities (``_uv``, ``_build_bub_requirement``, etc.) but own
their docstrings, argument annotations, and channel behavior.
"""

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
RUNTIME_COMMAND_PANELS: dict[str, str] = {
    "chat": "Runtime",
    "gateway": "Runtime",
    "turn": "Runtime",
    "plugin": "Environment",
    "mcp": "Environment",
    "onboard": "Environment",
    "login": "Environment",
}
PLUGIN_COMMAND_NAMES: tuple[str, ...] = ("install", "uninstall", "update")


def agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


# ---------------------------------------------------------------------------
# AgentSeek command implementations (replace Bub builtins at registration time)
# ---------------------------------------------------------------------------


def resolve_enabled_channels(framework, primary_channels: Iterable[str]) -> list[str]:
    """Enable requested channels plus Bub support channels exposed as ``*.lifecycle``."""
    enabled = list(dict.fromkeys(primary_channels))
    for channel_name in framework.get_channels(lambda _message: None):
        if channel_name.endswith(".lifecycle") and channel_name not in enabled:
            enabled.append(channel_name)
    return enabled


def _agentseek_chat(
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


def _agentseek_onboard(ctx: typer.Context) -> None:
    """Interactively collect plugin configuration and write it to the AgentSeek config file."""
    from bub import configure
    from bub.framework import BubFramework

    framework = ctx.ensure_object(BubFramework)
    typer.echo(AGENTSEEK_ONBOARD_BANNER.format(version=agentseek_version()))
    typer.echo(AGENTSEEK_ONBOARD_WELCOME)

    try:
        config_data = framework.collect_onboard_config()
        configure.save(framework.config_file, config_data)
    except (typer.Abort, typer.Exit):
        raise
    except Exception as exc:
        typer.secho(f"Onboarding failed: {exc}", err=True, fg="red")
        raise typer.Exit(1) from exc

    typer.echo(f"Saved config to {framework.config_file}")


def _default_plugin_project() -> Path:
    """Resolve the plugin environment directory via ``bub.home`` (configured by env aliases)."""
    from bub.builtin.cli import _default_project

    return _default_project()


def _ensure_plugin_sandbox(project: Path) -> None:
    """Ensure the AgentSeek plugin sandbox exists and is initialized."""
    from bub.builtin.cli import _build_bub_requirement, _uv

    project.mkdir(parents=True, exist_ok=True)
    if (project / "pyproject.toml").is_file():
        return
    _uv("init", "--bare", "--name", DEFAULT_PLUGIN_SANDBOX, "--app", cwd=project)
    bub_requirement = _build_bub_requirement()
    _uv("add", "--active", "--no-sync", *bub_requirement, cwd=project)


def _build_agentseek_requirement(spec: str) -> str:
    """Resolve a plugin spec, routing ``agentseek-*`` packages directly."""
    from bub.builtin.cli import _build_requirement as _bub_build_requirement

    if spec.startswith(("git@", "https://")) or "/" in spec:
        return _bub_build_requirement(spec)
    name, _, _ = spec.partition("@")
    if name.startswith("agentseek-"):
        return name
    return _bub_build_requirement(spec)


_project_opt = typer.Option(
    default_factory=_default_plugin_project,
    help="Path to the plugin environment directory.",
    envvar="BUB_PROJECT",
    show_envvar=False,
)
_specs_arg = typer.Argument(
    default_factory=list,
    help="Package spec: a git URL, owner/repo, or package name.",
)
_packages_arg = typer.Argument(..., help="Package name to uninstall.")
_packages_optional_arg = typer.Argument(
    default_factory=list,
    help="Package name to update, or omit to update all.",
)


def _agentseek_plugin_install(
    specs: list[str] = _specs_arg,
    project: Path = _project_opt,
) -> None:
    """Install a plugin into the AgentSeek environment, or sync if no specs are given."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    if not specs:
        _uv("sync", "--active", "--inexact", cwd=project)
    else:
        _uv("add", "--active", *map(_build_agentseek_requirement, specs), cwd=project)


def _agentseek_plugin_uninstall(
    packages: list[str] = _packages_arg,
    project: Path = _project_opt,
) -> None:
    """Uninstall a plugin from the AgentSeek environment."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    _uv("remove", "--active", *packages, cwd=project)


def _agentseek_plugin_update(
    packages: list[str] = _packages_optional_arg,
    project: Path = _project_opt,
) -> None:
    """Update selected packages or all packages in the AgentSeek environment."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    if not packages:
        _uv("sync", "--active", "--upgrade", "--inexact", cwd=project)
    else:
        package_args: list[str] = []
        for pkg in packages:
            package_args.extend(["--upgrade-package", pkg])
        _uv("sync", "--active", "--inexact", *package_args, cwd=project)


# ---------------------------------------------------------------------------
# Command layout — pop Bub commands, register AgentSeek replacements
# ---------------------------------------------------------------------------


def _command_name(command: typer.models.CommandInfo) -> str | None:
    if command.name:
        return command.name
    if command.callback is None:
        return None
    return getattr(command.callback, "__name__", None)


def _pop_registered_command(app: typer.Typer, name: str) -> typer.models.CommandInfo | None:
    for index, command in enumerate(app.registered_commands):
        if _command_name(command) == name:
            return app.registered_commands.pop(index)
    return None


def _tag_registered_command_panels(app: typer.Typer) -> None:
    for group in app.registered_groups:
        name = getattr(group, "name", None) or (group.typer_instance.info.name if group.typer_instance else None)
        if name and name in RUNTIME_COMMAND_PANELS and group.typer_instance:
            group.typer_instance.info.rich_help_panel = RUNTIME_COMMAND_PANELS[name]

    for command in app.registered_commands:
        name = _command_name(command)
        if name and name in RUNTIME_COMMAND_PANELS:
            command.rich_help_panel = RUNTIME_COMMAND_PANELS[name]


def apply_agentseek_runtime_command_layout(app: typer.Typer) -> None:
    """Replace Bub builtin commands with AgentSeek implementations and reorganize the layout."""
    app.suggest_commands = False

    # run → turn (reuse bub's callback unchanged)
    run_command = _pop_registered_command(app, "run")
    if run_command and run_command.callback is not None:
        app.command("turn", rich_help_panel=RUNTIME_COMMAND_PANELS["turn"])(run_command.callback)

    # chat → AgentSeek chat (lifecycle channels enabled)
    _pop_registered_command(app, "chat")
    app.command("chat", rich_help_panel=RUNTIME_COMMAND_PANELS["chat"])(_agentseek_chat)

    # onboard → AgentSeek onboard (branded)
    _pop_registered_command(app, "onboard")
    app.command("onboard", rich_help_panel=RUNTIME_COMMAND_PANELS["onboard"])(_agentseek_onboard)

    # install/uninstall/update → plugin group (AgentSeek implementations)
    plugin_app = typer.Typer(
        name="plugin",
        help="Manage AgentSeek runtime plugins.",
        add_completion=False,
        no_args_is_help=True,
    )
    for command_name in PLUGIN_COMMAND_NAMES:
        _pop_registered_command(app, command_name)
    plugin_app.command("install")(_agentseek_plugin_install)
    plugin_app.command("uninstall")(_agentseek_plugin_uninstall)
    plugin_app.command("update")(_agentseek_plugin_update)

    if not any(group.name == "plugin" for group in app.registered_groups):
        app.add_typer(plugin_app, name="plugin", rich_help_panel=RUNTIME_COMMAND_PANELS["plugin"])

    _tag_registered_command_panels(app)


__all__ = [
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "agentseek_version",
    "apply_agentseek_runtime_command_layout",
    "resolve_enabled_channels",
]
