from __future__ import annotations

import shutil
import subprocess


def test_agentseek_command_shows_help() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "--help"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "Usage:" in result.stdout
