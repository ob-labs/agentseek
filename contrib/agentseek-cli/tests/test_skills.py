from __future__ import annotations

import subprocess
from pathlib import Path

from agentseek_cli.app import build_app
from agentseek_cli.commands import skills as skills_module
from typer.testing import CliRunner


class _CompletedProcessStub:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def _stub_subprocess_run(captured: dict[str, object], *, returncode: int = 0):
    def _run(cmd, cwd=None, check=False):
        captured["cmd"] = list(cmd)
        captured["cwd"] = cwd
        captured["check"] = check
        return _CompletedProcessStub(returncode)

    return _run


def _stub_find_npx_skills(monkeypatch) -> None:
    monkeypatch.setattr(skills_module, "_find_npx_skills", lambda: "/usr/bin/npx-skills")


def test_skills_add_forwards_to_npx_skills(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    _stub_find_npx_skills(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(
        build_app(),
        ["skills", "--dir", str(tmp_path), "add", "vercel-labs/agent-skills", "--list"],
    )

    assert result.exit_code == 0
    assert captured["cmd"] == [
        "/usr/bin/npx-skills",
        "add",
        "vercel-labs/agent-skills",
        "--list",
    ]
    assert Path(str(captured["cwd"])).resolve() == tmp_path.resolve()


def test_skills_list_defaults_cwd_to_current_dir(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_npx_skills(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(build_app(), ["skills", "list"])

    assert result.exit_code == 0
    assert captured["cmd"] == ["/usr/bin/npx-skills", "list"]
    assert Path(str(captured["cwd"])).resolve() == Path.cwd().resolve()


def test_skills_propagates_non_zero_exit_code(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_npx_skills(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=42))

    result = CliRunner().invoke(build_app(), ["skills", "find", "typescript"])
    assert result.exit_code == 42


def test_skills_reports_missing_npx_skills(monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: None)

    result = CliRunner().invoke(build_app(), ["skills", "list"])
    assert result.exit_code == 1
    assert "npx-skills" in result.stderr


def test_skills_passes_all_documented_subcommands(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_npx_skills(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    runner = CliRunner()
    for sub in skills_module.SKILLS_COMMANDS:
        result = runner.invoke(build_app(), ["skills", sub])
        assert result.exit_code == 0, sub
        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        assert cmd[1] == sub
