from __future__ import annotations

import shutil
import stat
import tarfile
import zipfile
from pathlib import Path

DEFAULT_MAX_MEMBER_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_MEMBERS = 200
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".bz2", ".xz"}
SUPPORTED_MANIFEST_NAMES = {"manifest.yml", "manifest.yaml"}


def scan_images(directory: Path) -> list[Path]:
    images: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.is_file():
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


def _reject_oversized(member_name: str, size: int, max_member_bytes: int) -> None:
    if size > max_member_bytes:
        raise ValueError(f"Archive member too large: {member_name}")


def _track_expanded_member(
    member_name: str,
    size: int,
    total_bytes: int,
    member_count: int,
    max_total_bytes: int,
    max_members: int,
) -> tuple[int, int]:
    member_count += 1
    if member_count > max_members:
        raise ValueError(f"Too many archive members: {member_name}")
    total_bytes += size
    if total_bytes > max_total_bytes:
        raise ValueError(f"Archive expands beyond allowed size: {member_name}")
    return total_bytes, member_count


def _is_zip_symlink(member: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(member.external_attr >> 16)


def extract_archive_safely(
    source: Path,
    target: Path,
    *,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_total_bytes: int | None = None,
    max_members: int = DEFAULT_MAX_MEMBERS,
) -> Path:
    max_total_bytes = max_total_bytes or max_member_bytes
    total_bytes = 0
    member_count = 0
    target.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(source) as zf:
            for member in zf.infolist():
                destination = _safe_target(target, member.filename)
                if member.is_dir() or not _is_supported_member(member.filename):
                    continue
                if _is_zip_symlink(member):
                    raise ValueError(f"Unsupported archive member: {member.filename}")
                _reject_oversized(member.filename, member.file_size, max_member_bytes)
                total_bytes, member_count = _track_expanded_member(
                    member.filename,
                    member.file_size,
                    total_bytes,
                    member_count,
                    max_total_bytes,
                    max_members,
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source_fh, destination.open("wb") as destination_fh:
                    shutil.copyfileobj(source_fh, destination_fh)
        return target
    if suffix in SUPPORTED_ARCHIVE_SUFFIXES - {".zip"}:
        with tarfile.open(source) as tf:
            for member in tf.getmembers():
                destination = _safe_target(target, member.name)
                if member.isdir() or not _is_supported_member(member.name):
                    continue
                if not member.isfile():
                    raise ValueError(f"Unsupported archive member: {member.name}")
                _reject_oversized(member.name, member.size, max_member_bytes)
                total_bytes, member_count = _track_expanded_member(
                    member.name,
                    member.size,
                    total_bytes,
                    member_count,
                    max_total_bytes,
                    max_members,
                )
                extracted = tf.extractfile(member)
                if extracted is None:
                    raise ValueError(f"Unsupported archive member: {member.name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with extracted, destination.open("wb") as destination_fh:
                    shutil.copyfileobj(extracted, destination_fh)
        return target
    raise ValueError(f"Unsupported archive type: {source.suffix}")
