from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentseek_cli.commands.ctx import CTX_PASSTHROUGH_COMMANDS, app

runner = CliRunner()


def test_passthrough_commands_count() -> None:
    assert len(CTX_PASSTHROUGH_COMMANDS) == 18


def test_missing_contextseek_exits_with_error() -> None:
    with patch.dict("sys.modules", {"contextseek": None}):
        result = runner.invoke(app, ["add", "--help"])
    assert result.exit_code == 1


def test_sync_requires_scope() -> None:
    with patch("agentseek_cli.commands.ctx._require_contextseek"):
        result = runner.invoke(app, ["sync"])
    # Missing required --scope option.
    assert result.exit_code != 0


@pytest.mark.parametrize("cmd", CTX_PASSTHROUGH_COMMANDS)
def test_passthrough_registered(cmd: str) -> None:
    commands = {c.name for c in app.registered_commands}
    assert cmd in commands
