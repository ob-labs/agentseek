from __future__ import annotations

import typer
from agentseek_cli.app import build_app, iter_command_groups
from agentseek_cli.plugin import FRAMEWORK_OWNED_NAMES, AgentSeekCliPlugin
from typer.testing import CliRunner

EXPECTED_GROUPS = ("create", "run", "build", "deploy", "api", "skills")
PLUGIN_MOUNTED_GROUPS = tuple(name for name in EXPECTED_GROUPS if name not in FRAMEWORK_OWNED_NAMES)


def test_build_app_registers_every_documented_group() -> None:
    """Standalone (uvx) shape: all documented groups present, including framework-owned names."""
    app = build_app()
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(EXPECTED_GROUPS)


def test_build_app_help_lists_groups() -> None:
    result = CliRunner().invoke(build_app(), ["--help"])
    assert result.exit_code == 0
    for name in EXPECTED_GROUPS:
        assert name in result.stdout


def test_plugin_register_cli_commands_skips_framework_owned_names() -> None:
    """Plugin shape: skip names the framework's own plugins already provide (e.g. `run`)."""
    app = typer.Typer()
    AgentSeekCliPlugin().register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(PLUGIN_MOUNTED_GROUPS)
    for skipped in FRAMEWORK_OWNED_NAMES:
        assert skipped not in names


def test_plugin_register_cli_commands_is_idempotent() -> None:
    app = typer.Typer()
    plugin = AgentSeekCliPlugin()
    plugin.register_cli_commands(app)
    plugin.register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    for expected in PLUGIN_MOUNTED_GROUPS:
        assert names.count(expected) == 1


def test_iter_command_groups_preserves_documented_order() -> None:
    names = [sub.info.name for sub in iter_command_groups()]
    assert names == list(EXPECTED_GROUPS)
