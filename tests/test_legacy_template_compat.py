"""Regression tests for the published-client compatibility harness."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import check_legacy_template_compat as compatibility


def test_cookiecutter_generation_renders_candidate_through_explicit_repository(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    candidate = "0123456789abcdef0123456789abcdef01234567"
    commands: list[list[str]] = []
    monkeypatch.setattr(
        compatibility,
        "_run",
        lambda command, **_kwargs: commands.append(command) or "",
    )
    monkeypatch.setattr(compatibility, "_assert_v1_lifecycle", lambda *_args: None)

    compatibility._render_phase(
        ["uvx", "--from", "agentseek-cli==0.0.1", "agentseek", "create"],
        env={},
        output_root=tmp_path,
        checkout=candidate,
        explicit_repository=True,
    )

    assert len(commands) == len(compatibility.REPRESENTATIVE_TEMPLATES)
    for command, template in zip(commands, compatibility.REPRESENTATIVE_TEMPLATES, strict=True):
        assert command[-6:] == [
            compatibility.CORE_REPOSITORY,
            "--template",
            f"templates/{template}",
            "--no-input",
            "--checkout",
            candidate,
        ]


def test_repair_listing_stays_on_candidate_commit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    candidate = "0123456789abcdef0123456789abcdef01234567"
    commands: list[list[str]] = []
    render_cache = tmp_path / "render-state" / "cookiecutter"
    cached_index = render_cache / "agentseek" / "templates" / "index.json"

    monkeypatch.setattr(compatibility.shutil, "which", lambda _name: "/usr/bin/uvx")

    def fake_environment(work_root: Path, name: str) -> tuple[dict[str, str], Path]:
        cache = work_root / name / "cookiecutter"
        cache.mkdir(parents=True, exist_ok=True)
        return {"AGENTSEEK_TEST_STATE": name}, cache

    def fake_run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
        del cwd
        commands.append(command)
        if env["AGENTSEEK_TEST_STATE"] == "render-state" and "--template" in command:
            cached_index.parent.mkdir(parents=True, exist_ok=True)
            cached_index.write_text("{}", encoding="utf-8")
        return "\n".join(compatibility.REPRESENTATIVE_TEMPLATES)

    monkeypatch.setattr(compatibility, "_catalog_environment", fake_environment)
    monkeypatch.setattr(compatibility, "_run", fake_run)
    monkeypatch.setattr(
        compatibility,
        "_render_phase",
        lambda *_args, **_kwargs: (
            cached_index.parent.mkdir(parents=True, exist_ok=True) or cached_index.write_text("{}", encoding="utf-8")
        ),
    )
    monkeypatch.setattr(compatibility, "_assert_cache_commit", lambda *_args, **_kwargs: None)

    compatibility.verify_release("0.0.5", work_root=tmp_path, candidate_ref=candidate)

    repaired_listing = commands[-1]
    assert repaired_listing[-3:] == ["--template", "--checkout", candidate]
