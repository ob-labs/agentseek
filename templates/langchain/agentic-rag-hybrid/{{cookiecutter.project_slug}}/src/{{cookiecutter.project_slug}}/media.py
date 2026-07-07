from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".bz2", ".xz"}
SUPPORTED_MANIFEST_NAMES = {"manifest.yml", "manifest.yaml"}


def scan_images(directory: Path) -> list[Path]:
    images: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if "__MACOSX" in path.parts:
            continue
        if path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
            images.append(path)
    return images


def _safe_target(root: Path, member_name: str) -> Path:
    target = (root / member_name).resolve()
    root_resolved = root.resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f"Unsafe archive member: {member_name}")
    return target


def _is_supported_member(member_name: str) -> bool:
    path = Path(member_name)
    if not path.name or path.name.startswith("."):
        return False
    if "__MACOSX" in path.parts:
        return False
    return path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES or path.name in SUPPORTED_MANIFEST_NAMES


def extract_archive_safely(source: Path, target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(source) as zf:
            for member in zf.infolist():
                _safe_target(target, member.filename)
                if member.is_dir() or not _is_supported_member(member.filename):
                    continue
                zf.extract(member, target)
        return target
    if suffix in SUPPORTED_ARCHIVE_SUFFIXES - {".zip"}:
        with tarfile.open(source) as tf:
            for member in tf.getmembers():
                _safe_target(target, member.name)
                if member.isdir() or not _is_supported_member(member.name):
                    continue
                tf.extract(member, target)
        return target
    raise ValueError(f"Unsupported archive type: {source.suffix}")
