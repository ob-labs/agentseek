from __future__ import annotations

import shutil
import subprocess


def test_agentseek_command_shows_help() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "--help"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "AGENTSEEK v" in result.stdout


def test_agentseek_version_shows_banner() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "version"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "AGENTSEEK v" in result.stdout


def test_agentseek_invalid_mode_exits_without_traceback() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run(  # noqa: S603
        [command, "--mode", "nope", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unsupported CLI mode: nope" in result.stderr
    assert "Traceback" not in result.stderr


def test_logfire_console_config_maps_bool_to_runtime_config() -> None:
    from logfire import ConsoleOptions

    import agentseek.__main__ as entrypoint

    disabled = entrypoint._logfire_console_config(False)
    enabled = entrypoint._logfire_console_config(True)

    assert disabled is False
    assert isinstance(enabled, ConsoleOptions)
    assert enabled.verbose is False
