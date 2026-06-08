"""Tests for ``agentseek ctx`` — verify forwarding to the contextseek CLI.

The point of this module is that it owns *no* command list, so all tests live
on a synthetic ``run_cli`` recorder. Real upstream behaviour (verb names,
exit codes, help text) is contextseek's responsibility, not ours.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from typer.testing import CliRunner

from agentseek.lifecycle.commands import ctx as ctx_module


class _RunCliRecorder:
    """Stand-in for ``contextseek.cli.run_cli``."""

    def __init__(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code
        self.calls: list[list[str]] = []

    def __call__(self, argv: Sequence[str]) -> int:
        self.calls.append(list(argv))
        return self.exit_code


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _RunCliRecorder:
    rec = _RunCliRecorder()
    monkeypatch.setattr(ctx_module, "_load_contextseek_run_cli", lambda: rec)
    return rec


def test_forwards_known_verb_with_args(recorder: _RunCliRecorder) -> None:
    result = CliRunner().invoke(ctx_module.app, ["add", "--scope", "p", "hello"])
    assert result.exit_code == 0
    assert recorder.calls == [["add", "--scope", "p", "hello"]]


def test_forwards_unknown_verb_verbatim(recorder: _RunCliRecorder) -> None:
    """We never enumerate upstream verbs; brand-new verbs must work."""
    result = CliRunner().invoke(ctx_module.app, ["future-verb", "x", "--y"])
    assert result.exit_code == 0
    assert recorder.calls == [["future-verb", "x", "--y"]]


def test_help_is_forwarded(recorder: _RunCliRecorder) -> None:
    """``agentseek ctx --help`` must show contextseek's own help, not ours."""
    result = CliRunner().invoke(ctx_module.app, ["--help"])
    assert result.exit_code == 0
    assert recorder.calls == [["--help"]]


def test_no_args_forwards_help(recorder: _RunCliRecorder) -> None:
    result = CliRunner().invoke(ctx_module.app, [])
    assert result.exit_code == 0
    assert recorder.calls == [["--help"]]


def test_propagates_upstream_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ctx_module, "_load_contextseek_run_cli", lambda: _RunCliRecorder(exit_code=7))
    result = CliRunner().invoke(ctx_module.app, ["retrieve", "--scope", "p"])
    assert result.exit_code == 7


def test_reports_missing_contextseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ctx_module,
        "_load_contextseek_run_cli",
        lambda: (_ for _ in ()).throw(ctx_module.MissingContextSeekError()),
    )
    result = CliRunner().invoke(ctx_module.app, ["add"])
    assert result.exit_code == 1
    assert "contextseek" in result.stderr


def test_missing_contextseek_help_is_discoverable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ctx_module,
        "_load_contextseek_run_cli",
        lambda: (_ for _ in ()).throw(ctx_module.MissingContextSeekError()),
    )
    result = CliRunner().invoke(ctx_module.app, ["--help"])
    assert result.exit_code == 0
    assert "agentseek plugin install agentseek-contextseek" in result.output
