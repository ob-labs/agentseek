"""Helpers for bundled skills discovery and workspace installation."""

from __future__ import annotations

import shutil
from pathlib import Path

SKILL_FILE_NAME = "SKILL.md"


def bundled_skill_names() -> list[str]:
    """Return bundled skill names in deterministic order."""
    names: list[str] = []
    for entry in _skills_root().iterdir():
        if not entry.is_dir():
            continue
        if not entry.joinpath(SKILL_FILE_NAME).is_file():
            continue
        names.append(entry.name)
    return sorted(names)


def install_skills_to_workspace(workspace: str | Path, *, overwrite: bool = False) -> list[Path]:
    """Copy bundled skills into workspace `.agents/skills`."""
    workspace_path = Path(workspace).expanduser().resolve()
    installed: list[Path] = []

    for skill_name in bundled_skill_names():
        source_dir = _skills_root() / skill_name
        target = install_skill_dir(source_dir=source_dir, skill_name=skill_name, workspace=workspace_path, overwrite=overwrite)
        if target is not None:
            installed.append(target)

    return installed


def install_skill_dir(*, source_dir: Path, skill_name: str, workspace: str | Path, overwrite: bool = False) -> Path | None:
    """Copy one skill directory into workspace `.agents/skills/<skill_name>`."""
    workspace_path = Path(workspace).expanduser().resolve()
    target_dir = workspace_path / ".agents" / "skills" / skill_name
    target = target_dir / SKILL_FILE_NAME
    if target_dir.exists() and not overwrite:
        return None
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)
    return target


def _skills_root() -> Path:
    root = _distribution_root()
    path = root / "skills"
    if path.is_dir():
        return path
    package_local = Path(__file__).resolve().parent / "skills"
    if package_local.is_dir():
        return package_local
    raise FileNotFoundError("bubseek skills directory not found")


def _distribution_root() -> Path:
    # source tree: <repo>/packages/bubseek/src/bubseek/skills.py
    # installed:   <venv>/site-packages/bubseek/skills.py
    return Path(__file__).resolve().parents[2]
