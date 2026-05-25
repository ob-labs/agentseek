from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from agentseek_cli.app import build_app
from agentseek_cli.commands import api as api_module
from typer.testing import CliRunner


class _FakeAgentSeekApiCliModule:
    def __init__(self, exit_code: int, captured: dict[str, object]) -> None:
        self._exit_code = exit_code
        self._captured = captured

    def main(
        self,
        argv: Sequence[str] | None = None,
        *,
        prog: str | None = None,
        cwd: str | Path | None = None,
    ) -> int:
        self._captured["argv"] = list(argv or [])
        self._captured["prog"] = prog
        self._captured["cwd"] = cwd
        return self._exit_code


def test_api_help_lists_documented_verbs() -> None:
    result = CliRunner().invoke(build_app(), ["api", "--help"])
    assert result.exit_code == 0
    for verb in api_module.API_COMMANDS:
        assert verb in result.stdout


def test_api_forwards_arguments_to_agentseek_api(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_module = _FakeAgentSeekApiCliModule(exit_code=7, captured=captured)

    monkeypatch.setattr(api_module.importlib, "import_module", lambda name: fake_module)

    result = CliRunner().invoke(build_app(), ["api", "dev", "--port", "9911", "--no-reload"])

    assert result.exit_code == 7
    assert captured["argv"] == ["dev", "--port", "9911", "--no-reload"]
    assert captured["prog"] == "agentseek api"
    assert captured["cwd"] == Path.cwd().resolve()


def test_api_reports_missing_agentseek_api_dependency(monkeypatch) -> None:
    def fail_import(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(api_module.importlib, "import_module", fail_import)

    result = CliRunner().invoke(build_app(), ["api", "version"])

    assert result.exit_code == 1
    assert "agentseek-api" in result.stderr


def test_api_reraises_unrelated_module_errors(monkeypatch) -> None:
    def fail_import(name: str):
        raise ModuleNotFoundError("totally_other_package")

    monkeypatch.setattr(api_module.importlib, "import_module", fail_import)

    result = CliRunner().invoke(build_app(), ["api", "version"])
    # Should not have been masked as missing-agentseek-api error.
    assert result.exit_code != 0
    assert isinstance(result.exception, ModuleNotFoundError)
