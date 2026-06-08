from __future__ import annotations

import typer

from agentseek.lifecycle.app import iter_command_groups, mount_lifecycle_commands
from tests.lifecycle.helpers import build_lifecycle_app

EXPECTED_GROUPS = ("new", "dev", "build", "deploy", "api", "ctx", "skills")
LEGACY_ROOT_FORMS = ("run", "create", "install", "uninstall", "update")


def test_mount_lifecycle_commands_registers_every_documented_group() -> None:
    app = build_lifecycle_app()
    names = [group.name for group in app.registered_groups]
    assert names == list(EXPECTED_GROUPS)


def test_mount_lifecycle_commands_rejects_legacy_root_forms_structurally() -> None:
    app = build_lifecycle_app()
    names = {group.name for group in app.registered_groups}
    names.update(command.name for command in app.registered_commands if command.name)

    assert app.suggest_commands is False
    assert names.isdisjoint(LEGACY_ROOT_FORMS)


def test_mount_lifecycle_commands_does_not_override_existing_names() -> None:
    app = typer.Typer()
    dummy_dev = typer.Typer(name="dev", help="Framework dev should stay.")
    app.add_typer(dummy_dev, name="dev")

    mount_lifecycle_commands(app)

    dev_groups = [group for group in app.registered_groups if group.name == "dev"]
    assert len(dev_groups) == 1
    assert dev_groups[0].typer_instance is dummy_dev


def test_mount_lifecycle_commands_is_idempotent() -> None:
    app = typer.Typer()
    mount_lifecycle_commands(app)
    mount_lifecycle_commands(app)

    names = [group.name for group in app.registered_groups]
    for expected in EXPECTED_GROUPS:
        assert names.count(expected) == 1


def test_iter_command_groups_preserves_documented_order() -> None:
    names = [group.name for group in iter_command_groups()]
    assert names == list(EXPECTED_GROUPS)
