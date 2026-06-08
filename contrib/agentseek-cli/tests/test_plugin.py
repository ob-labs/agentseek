from __future__ import annotations

import typer
from agentseek_cli.app import build_app, iter_command_groups, register_version_command
from agentseek_cli.plugin import AgentSeekCliPlugin
from typer.testing import CliRunner

EXPECTED_GROUPS = ("new", "dev", "build", "deploy", "api", "ctx", "skills")
VERSION_COMMAND = "version"


def test_build_app_registers_every_documented_group() -> None:
    """Standalone (uvx) shape: all documented groups present."""
    app = build_app()
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(EXPECTED_GROUPS)
    assert [command.name for command in app.registered_commands].count(VERSION_COMMAND) == 1


def test_build_app_help_lists_groups() -> None:
    result = CliRunner().invoke(build_app(), ["--help"])
    assert result.exit_code == 0
    for name in EXPECTED_GROUPS:
        assert name in result.stdout
    assert VERSION_COMMAND in result.stdout


def test_build_app_version_reports_cli_package() -> None:
    result = CliRunner().invoke(build_app(), [VERSION_COMMAND])
    assert result.exit_code == 0
    assert "agentseek-cli" in result.stdout


def test_plugin_register_cli_commands_does_not_override_framework_names() -> None:
    """Plugin shape: existing framework names are left untouched."""
    app = typer.Typer()
    dummy_dev = typer.Typer(name="dev", help="Framework dev (should stay).")
    app.add_typer(dummy_dev, name="dev")

    AgentSeekCliPlugin().register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    assert names.count("dev") == 1

    dev_groups = [g for g in app.registered_groups if g.name == "dev"]
    assert len(dev_groups) == 1
    assert dev_groups[0].typer_instance is dummy_dev


def test_plugin_register_cli_commands_mounts_all_groups() -> None:
    """Plugin shape: all expected groups are mounted."""
    app = typer.Typer()
    AgentSeekCliPlugin().register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(EXPECTED_GROUPS)
    assert [command.name for command in app.registered_commands].count(VERSION_COMMAND) == 1


def test_plugin_register_cli_commands_is_idempotent() -> None:
    app = typer.Typer()
    plugin = AgentSeekCliPlugin()
    plugin.register_cli_commands(app)
    plugin.register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    for expected in EXPECTED_GROUPS:
        assert names.count(expected) == 1
    assert [command.name for command in app.registered_commands].count(VERSION_COMMAND) == 1


def test_register_version_command_is_idempotent() -> None:
    app = typer.Typer()
    register_version_command(app)
    register_version_command(app)

    assert [command.name for command in app.registered_commands] == [VERSION_COMMAND]


def test_iter_command_groups_preserves_documented_order() -> None:
    names = [group.name for group in iter_command_groups()]
    assert names == list(EXPECTED_GROUPS)
