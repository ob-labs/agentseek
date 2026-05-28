from __future__ import annotations

import typer
from agentseek_cli.app import build_app, iter_command_groups
from agentseek_cli.plugin import AgentSeekCliPlugin
from typer.testing import CliRunner

EXPECTED_GROUPS = ("create", "run", "build", "deploy", "api", "ctx", "skills")


def test_build_app_registers_every_documented_group() -> None:
    """Standalone (uvx) shape: all documented groups present."""
    app = build_app()
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(EXPECTED_GROUPS)


def test_build_app_help_lists_groups() -> None:
    result = CliRunner().invoke(build_app(), ["--help"])
    assert result.exit_code == 0
    for name in EXPECTED_GROUPS:
        assert name in result.stdout


def test_plugin_register_cli_commands_overrides_framework_run() -> None:
    """Plugin shape: cli's ``run`` replaces any pre-existing ``run`` command."""
    from agentseek_cli.commands.run import app as cli_run_app

    # Simulate a pre-existing framework ``run`` command.
    app = typer.Typer()
    dummy_run = typer.Typer(name="run", help="Framework run (should be replaced).")
    app.add_typer(dummy_run, name="run")

    AgentSeekCliPlugin().register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    assert names.count("run") == 1

    # Verify it's the cli's run, not the dummy.
    run_groups = [g for g in app.registered_groups if g.name == "run"]
    assert len(run_groups) == 1
    assert run_groups[0].typer_instance is cli_run_app


def test_plugin_register_cli_commands_mounts_all_groups() -> None:
    """Plugin shape: all expected groups are mounted."""
    app = typer.Typer()
    AgentSeekCliPlugin().register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    assert set(names) == set(EXPECTED_GROUPS)


def test_plugin_register_cli_commands_is_idempotent() -> None:
    app = typer.Typer()
    plugin = AgentSeekCliPlugin()
    plugin.register_cli_commands(app)
    plugin.register_cli_commands(app)
    names = [group.name for group in app.registered_groups]
    for expected in EXPECTED_GROUPS:
        assert names.count(expected) == 1


def test_iter_command_groups_preserves_documented_order() -> None:
    names = [sub.info.name for sub in iter_command_groups()]
    assert names == list(EXPECTED_GROUPS)
