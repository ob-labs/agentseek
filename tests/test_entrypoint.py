from __future__ import annotations

import shutil
import subprocess
from types import SimpleNamespace


def test_agentseek_command_shows_help() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "--help"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_agentseek_bootstrap_enables_observability_when_available(monkeypatch) -> None:
    import agentseek.__main__ as entrypoint

    calls: list[str] = []

    def fake_import_module(name: str):
        if name == "agentseek_observability.plugin":
            return SimpleNamespace(instrument_agentseek_observability=lambda: calls.append(name))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(entrypoint.importlib, "import_module", fake_import_module)

    entrypoint._maybe_enable_observability()

    assert calls == ["agentseek_observability.plugin"]


def test_agentseek_bootstrap_skips_missing_observability(monkeypatch) -> None:
    import agentseek.__main__ as entrypoint

    monkeypatch.setattr(
        entrypoint.importlib,
        "import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError(name)),
    )

    entrypoint._maybe_enable_observability()


def test_logfire_console_config_maps_bool_to_runtime_config() -> None:
    from logfire import ConsoleOptions

    import agentseek.__main__ as entrypoint

    disabled = entrypoint._logfire_console_config(False)
    enabled = entrypoint._logfire_console_config(True)

    assert disabled is False
    assert isinstance(enabled, ConsoleOptions)
    assert enabled.verbose is False
