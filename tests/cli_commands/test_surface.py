from __future__ import annotations

import typer

from agentseek.cli import CommandCapability, iter_command_capabilities, mount_agentseek_commands
from tests.cli_commands.helpers import build_command_app

EXPECTED_GROUPS = ("create", "run", "build", "deploy", "api", "ctx", "skills")
LEGACY_ROOT_FORMS = ("new", "dev", "install", "uninstall", "update")


def test_mount_agentseek_commands_registers_every_documented_group() -> None:
    app = build_command_app()
    names = [group.name for group in app.registered_groups]
    assert names == list(EXPECTED_GROUPS)


def test_mount_agentseek_commands_rejects_legacy_root_forms_structurally() -> None:
    app = build_command_app()
    names = {group.name for group in app.registered_groups}
    names.update(command.name for command in app.registered_commands if command.name)

    assert app.suggest_commands is False
    assert names.isdisjoint(LEGACY_ROOT_FORMS)


def test_mount_agentseek_commands_does_not_override_existing_names() -> None:
    app = typer.Typer()
    dummy_run = typer.Typer(name="run", help="Framework run should stay.")
    app.add_typer(dummy_run, name="run")

    mount_agentseek_commands(app)

    run_groups = [group for group in app.registered_groups if group.name == "run"]
    assert len(run_groups) == 1
    assert run_groups[0].typer_instance is dummy_run


def test_mount_agentseek_commands_is_idempotent() -> None:
    app = typer.Typer()
    mount_agentseek_commands(app)
    mount_agentseek_commands(app)

    names = [group.name for group in app.registered_groups]
    for expected in EXPECTED_GROUPS:
        assert names.count(expected) == 1


def test_iter_command_capabilities_preserves_documented_order() -> None:
    names = [group.name for group in iter_command_capabilities()]
    assert names == list(EXPECTED_GROUPS)


def test_iter_command_capabilities_exposes_public_command_contract() -> None:
    capabilities = iter_command_capabilities()

    assert all(isinstance(capability, CommandCapability) for capability in capabilities)
    assert {capability.panel for capability in capabilities} == {"Project", "Services"}
    assert all(capability.summary for capability in capabilities)
    assert all(isinstance(capability.app, typer.Typer) for capability in capabilities)
