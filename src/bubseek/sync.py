"""Sync helpers that apply `bubseek.lock` to an environment/workspace."""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bubseek.config import (
    LockedBubEntry,
    LockedContribEntry,
    LockedSkillEntry,
    load_lock,
    locked_bub_entry,
    locked_contrib_entries,
    locked_skill_entries,
    resolve_config_path,
    sha256_dir,
    sha256_file,
    sha256_text,
    verify_local_package_dir,
)
from bubseek.skills import install_skill_dir

GIT_SOURCE_RE = re.compile(
    r"^git\+(?P<repo>[^@#]+?)(?:@(?P<ref>[^#]+))?(?:#subdirectory=(?P<subdirectory>.+))?$"
)
CACHE_DIR_ENV = "BUBSEEK_CACHE_DIR"
CACHE_KEY_FILE = ".bubseek-cache-key"


class BubseekSyncSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BUBSEEK_", extra="ignore", env_file=".env")

    cache_dir: Path = Field(default=Path.home() / ".cache" / "bubseek")


@dataclass(frozen=True)
class SyncResult:
    installed_bub: str | None = None
    installed_contrib: list[str] = field(default_factory=list)
    installed_skills: list[Path] = field(default_factory=list)
    skipped_skills: list[str] = field(default_factory=list)


def sync_from_lock(
    *,
    config_path: str | Path | None = None,
    lock_path: str | Path | None = None,
    workspace: str | Path = ".",
    sync_contrib: bool = True,
    sync_skills: bool = True,
    overwrite_skills: bool = False,
) -> SyncResult:
    """Apply lockfile by installing bubbled packages and synchronizing skills."""
    resolved_config_path = resolve_config_path(config_path)
    lock = load_lock(lock_path, config_path=resolved_config_path)
    _verify_lock_metadata(lock=lock, config_path=resolved_config_path)
    workspace_path = Path(workspace).expanduser().resolve()

    installed_bub: str | None = None
    installed_contrib: list[str] = []
    installed_skills: list[Path] = []
    skipped_skills: list[str] = []

    bub_entry = locked_bub_entry(lock)
    contrib_entries = locked_contrib_entries(lock) if sync_contrib else []
    if bub_entry is not None or contrib_entries:
        installed_bub, installed_contrib = _install_distribution_packages(
            bub_entry=bub_entry,
            contrib_entries=contrib_entries,
            config_root=resolved_config_path.parent,
        )

    if sync_skills:
        for skill_entry in locked_skill_entries(lock):
            skill_path = _sync_skill_entry(
                entry=skill_entry,
                config_root=resolved_config_path.parent,
                workspace=workspace_path,
                overwrite=overwrite_skills,
            )
            if skill_path is None:
                skipped_skills.append(skill_entry.name or "<unnamed>")
            else:
                installed_skills.append(skill_path)

    return SyncResult(
        installed_bub=installed_bub,
        installed_contrib=installed_contrib,
        installed_skills=installed_skills,
        skipped_skills=skipped_skills,
    )


def _install_distribution_packages(
    *,
    bub_entry: LockedBubEntry | None,
    contrib_entries: list[LockedContribEntry],
    config_root: Path,
) -> tuple[str | None, list[str]]:
    install_targets: list[str] = []
    installed_bub: str | None = None

    if bub_entry is not None:
        bub_target = _resolve_bub_install_target(entry=bub_entry, config_root=config_root)
        install_targets.append(str(bub_target))
        installed_bub = str(bub_target)

    for contrib_entry in contrib_entries:
        install_targets.append(str(_resolve_distribution_install_target(entry=contrib_entry, config_root=config_root)))

    if install_targets:
        _run_command(["uv", "pip", "install", "--no-sources", *install_targets])

    installed_contrib = [entry.name for entry in contrib_entries if entry.name is not None]
    return installed_bub, installed_contrib


def _resolve_bub_install_target(*, entry: LockedBubEntry, config_root: Path) -> Path:
    return _resolve_distribution_install_target(entry=entry, config_root=config_root)


def _resolve_distribution_install_target(*, entry: LockedBubEntry | LockedContribEntry, config_root: Path) -> Path:
    label = entry.name or "bub"
    if entry.kind == "local":
        if entry.path is None:
            raise ValueError(f"local install path missing: {label}")
        source_dir = (config_root / entry.path).resolve()
        verify_local_package_dir(
            path=source_dir,
            expected_sha256=entry.sha256,
            error_message=f"local package checksum mismatch: {label}",
        )
        return source_dir

    if entry.source is None:
        raise ValueError(f"remote install source missing: {label}")
    _verify_source_checksum(
        source=entry.source,
        expected_sha256=entry.sha256,
        error_message=f"remote package checksum mismatch: {label}",
    )
    return _resolve_cached_source_target(entry.source, source_kind=label)


def _sync_skill_entry(*, entry: LockedSkillEntry, config_root: Path, workspace: Path, overwrite: bool) -> Path | None:
    if entry.name is None:
        raise ValueError("skill name missing")
    source_dir = _resolve_skill_source(entry=entry, config_root=config_root)
    return _sync_skill_dir(source_dir=source_dir, skill_name=entry.name, workspace=workspace, overwrite=overwrite)


def _resolve_skill_source(*, entry: LockedSkillEntry, config_root: Path) -> Path:
    if entry.kind == "local":
        if entry.path is None:
            raise ValueError(f"local skill path missing: {entry.name}")
        source_dir = (config_root / entry.path).resolve()
        actual_sha256 = sha256_dir(source_dir)
        if actual_sha256 != entry.sha256:
            raise ValueError(f"local skill checksum mismatch: {entry.name}")
        return source_dir

    if entry.source is None:
        raise ValueError(f"remote skill source missing: {entry.name}")
    _verify_source_checksum(
        source=entry.source,
        expected_sha256=entry.sha256,
        error_message=f"remote skill checksum mismatch: {entry.name}",
    )
    return _resolve_cached_subdirectory(entry.source, source_kind="skill")


def _sync_skill_dir(*, source_dir: Path, skill_name: str, workspace: Path, overwrite: bool) -> Path | None:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"skill source directory not found: {source_dir}")
    if not (source_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"SKILL.md not found in: {source_dir}")
    return install_skill_dir(source_dir=source_dir, skill_name=skill_name, workspace=workspace, overwrite=overwrite)


@contextlib.contextmanager
def _remote_skill_dir(entry: LockedSkillEntry) -> Iterator[Path]:
    if entry.source is None:
        raise ValueError(f"remote skill source missing: {entry.name}")
    _verify_source_checksum(
        source=entry.source,
        expected_sha256=entry.sha256,
        error_message=f"remote skill checksum mismatch: {entry.name}",
    )
    yield _resolve_cached_subdirectory(entry.source, source_kind="skill")


def _parse_git_source(source: str) -> tuple[str, str | None, str | None]:
    matched = GIT_SOURCE_RE.match(source)
    if matched is None:
        raise ValueError(f"unsupported git source: {source}")
    return matched.group("repo"), matched.group("ref"), matched.group("subdirectory")


def _run_command(command: list[str]) -> None:
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError(f"command not found: {command[0]}")
    subprocess.run([executable, *command[1:]], check=True)


def _clone_repo(*, repo: str, ref: str | None, checkout_dir: Path) -> None:
    if ref is None:
        _run_command(["git", "clone", "--depth", "1", repo, str(checkout_dir)])
        return
    try:
        _run_command(["git", "clone", "--depth", "1", "--branch", ref, repo, str(checkout_dir)])
    except subprocess.CalledProcessError:
        _run_command(["git", "clone", repo, str(checkout_dir)])
        _run_command(["git", "-C", str(checkout_dir), "checkout", ref])


def _verify_lock_metadata(*, lock: dict[str, Any], config_path: Path) -> None:
    raw_meta = lock.get("meta")
    if not isinstance(raw_meta, dict):
        return
    expected_sha256 = raw_meta.get("config_sha256")
    if not isinstance(expected_sha256, str) or not expected_sha256.strip():
        return
    actual_sha256 = sha256_file(config_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(f"lock config checksum mismatch: {config_path}")


def _verify_source_checksum(*, source: str, expected_sha256: str, error_message: str) -> None:
    actual_sha256 = sha256_text(source)
    if actual_sha256 != expected_sha256:
        raise ValueError(error_message)


def _cache_root() -> Path:
    configured = os.getenv(CACHE_DIR_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return BubseekSyncSettings().cache_dir.expanduser().resolve()


def _resolve_cached_source_target(source: str, *, source_kind: str) -> Path:
    repo, ref, subdirectory = _parse_git_source(source)
    checkout_dir = _ensure_cached_checkout(repo=repo, ref=ref)
    target_dir = checkout_dir if subdirectory is None else checkout_dir / subdirectory
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        raise FileNotFoundError(f"{source_kind} source directory not found in cached checkout: {target_dir}")
    return target_dir


def _resolve_cached_subdirectory(source: str, *, source_kind: str) -> Path:
    _repo, _ref, subdirectory = _parse_git_source(source)
    if subdirectory is None:
        raise ValueError(f"{source_kind} source must include subdirectory: {source}")
    return _resolve_cached_source_target(source, source_kind=source_kind)


def _ensure_cached_checkout(*, repo: str, ref: str | None) -> Path:
    cache_key = _cache_key(repo=repo, ref=ref)
    checkout_dir = _cache_root() / "git" / cache_key
    marker_path = checkout_dir / CACHE_KEY_FILE
    expected_marker = _cache_marker(repo=repo, ref=ref)
    if checkout_dir.is_dir() and marker_path.is_file():
        cached_marker = marker_path.read_text(encoding="utf-8").strip()
        if cached_marker == expected_marker:
            return checkout_dir

    checkout_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bubseek-git-cache-") as tmp_dir:
        temp_checkout_dir = Path(tmp_dir) / "repo"
        _clone_repo(repo=repo, ref=ref, checkout_dir=temp_checkout_dir)
        (temp_checkout_dir / CACHE_KEY_FILE).write_text(expected_marker, encoding="utf-8")
        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)
        shutil.move(str(temp_checkout_dir), str(checkout_dir))
    return checkout_dir


def _cache_key(*, repo: str, ref: str | None) -> str:
    return sha256_text(_cache_marker(repo=repo, ref=ref))


def _cache_marker(*, repo: str, ref: str | None) -> str:
    return f"{repo}\n{ref or ''}"
