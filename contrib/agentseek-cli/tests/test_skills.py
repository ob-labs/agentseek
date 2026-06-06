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


def _stub_find_skills_cmd(monkeypatch) -> None:
    monkeypatch.setattr(skills_module, "_find_skills_cmd", lambda: ["/usr/bin/npx-skills"])


def test_skills_add_forwards_to_npx_skills(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
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


def test_skills_add_defaults_to_ob_labs_agentseek(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(
        build_app(),
        ["skills", "--dir", str(tmp_path), "add", "--all", "--global"],
    )

    assert result.exit_code == 0
    assert captured["cmd"] == [
        "/usr/bin/npx-skills",
        "add",
        "ob-labs/agentseek",
        "--all",
        "--global",
    ]


def test_skills_add_injects_default_when_only_flags_present(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(
        build_app(),
        ["skills", "add", "--skill", "langsmith-trace", "--global", "--yes"],
    )

    assert result.exit_code == 0
    assert captured["cmd"] == [
        "/usr/bin/npx-skills",
        "add",
        "ob-labs/agentseek",
        "--skill",
        "langsmith-trace",
        "--global",
        "--yes",
    ]


def test_skills_add_does_not_override_explicit_source(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(
        build_app(),
        ["skills", "add", "langchain-ai/langsmith-skills", "--skill", "*", "--yes"],
    )

    assert result.exit_code == 0
    assert captured["cmd"] == [
        "/usr/bin/npx-skills",
        "add",
        "langchain-ai/langsmith-skills",
        "--skill",
        "*",
        "--yes",
    ]


def test_skills_list_defaults_cwd_to_current_dir(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(build_app(), ["skills", "list"])

    assert result.exit_code == 0
    assert captured["cmd"] == ["/usr/bin/npx-skills", "list"]
    assert Path(str(captured["cwd"])).resolve() == Path.cwd().resolve()


def test_skills_propagates_non_zero_exit_code(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=42))

    result = CliRunner().invoke(build_app(), ["skills", "find", "typescript"])
    assert result.exit_code == 42


def test_skills_falls_back_to_npx(monkeypatch) -> None:
    import shutil

    captured: dict[str, object] = {}
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/npx" if name == "npx" else None)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    result = CliRunner().invoke(build_app(), ["skills", "list"])
    assert result.exit_code == 0
    assert captured["cmd"] == ["/usr/bin/npx", "skills", "list"]


def test_skills_reports_missing_both(monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: None)

    result = CliRunner().invoke(build_app(), ["skills", "list"])
    assert result.exit_code == 1
    assert "npx-skills" in result.output or "npx" in result.output


def test_skills_passes_all_documented_subcommands(monkeypatch) -> None:
    captured: dict[str, object] = {}
    _stub_find_skills_cmd(monkeypatch)
    monkeypatch.setattr(subprocess, "run", _stub_subprocess_run(captured, returncode=0))

    runner = CliRunner()
    for sub in skills_module.SKILLS_COMMANDS:
        result = runner.invoke(build_app(), ["skills", sub])
        assert result.exit_code == 0, sub
        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        # cmd is ["/usr/bin/npx-skills", <subcommand>, ...] with the stub
        assert sub in cmd
