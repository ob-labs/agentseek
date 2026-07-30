"""Immutable default template-catalog resolution."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import tarfile
import tempfile
import time
import uuid
import zlib
from base64 import urlsafe_b64encode
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any, Never
from urllib.parse import urlsplit

import httpx
from filelock import FileLock
from filelock import Timeout as FileLockTimeout

_LOCK_FIELDS = frozenset({
    "schema_version",
    "catalog_repository",
    "catalog_commit",
    "catalog_release",
    "templates_root",
    "index_path",
    "lifecycle_version",
    "core_repository",
    "core_commit",
    "core_release",
    "templates",
    "template_digests",
})
_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_KEY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_REPOSITORY_SEGMENT_PATTERN = re.compile(r"[A-Za-z0-9_.-]+\Z")
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"} | {f"COM{index}" for index in range(1, 10)} | {f"LPT{index}" for index in range(1, 10)}
)
# The coordinate itself is a SHA-256 digest. Keep its containing namespace
# compact so cache paths remain usable on Windows after template extraction.
_CACHE_NAMESPACE = ".l"
_CACHE_METADATA = ".agentseek-catalog-metadata.json"
_CACHE_SCHEMA_VERSION = 1
_CACHE_LOCK_TIMEOUT_SECONDS = 30.0
MAX_COMPRESSED_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_EXTENSION_DEPTH = 64
_DOWNLOAD_CONNECT_TIMEOUT_SECONDS = 10.0
_DOWNLOAD_READ_TIMEOUT_SECONDS = 30.0
_DOWNLOAD_OVERALL_TIMEOUT_SECONDS = 120.0


class CatalogError(ValueError):
    """The locked catalog cannot be trusted or prepared."""


def _fail(reason: str, *, cause: BaseException | None = None) -> Never:
    raise CatalogError(reason) from cause


def _validate_declared_member_size(size: int) -> None:
    if size < 0 or size > MAX_MEMBER_BYTES:
        _fail("catalog archive exceeds the 32 MiB member limit")


class _BoundedTarFile(tarfile.TarFile):
    """Tar reader state shared with raw-member processing."""

    agentseek_raw_member_count = 0
    agentseek_extension_depth = 0


class _BoundedTarInfo(tarfile.TarInfo):
    """Reject hidden tar metadata records before their payload is consumed."""

    def _proc_member(self, archive: tarfile.TarFile) -> tarfile.TarInfo:
        if not isinstance(archive, _BoundedTarFile):
            _fail("catalog archive reader is not bounded")
        archive.agentseek_raw_member_count += 1
        if archive.agentseek_raw_member_count > MAX_ARCHIVE_MEMBERS:
            _fail("catalog archive exceeds the 10,000 member limit")
        _validate_declared_member_size(self.size)

        extension_types = {
            tarfile.GNUTYPE_LONGNAME,
            tarfile.GNUTYPE_LONGLINK,
            tarfile.XHDTYPE,
            tarfile.XGLTYPE,
            tarfile.SOLARIS_XHDTYPE,
        }
        if self.type not in extension_types:
            return super()._proc_member(archive)  # ty: ignore[unresolved-attribute]

        archive.agentseek_extension_depth += 1
        try:
            if archive.agentseek_extension_depth > MAX_EXTENSION_DEPTH:
                _fail("catalog archive exceeds the extension nesting limit")
            return super()._proc_member(archive)  # ty: ignore[unresolved-attribute]
        finally:
            archive.agentseek_extension_depth -= 1


@dataclass(frozen=True)
class CatalogLock:
    """Validated schema-one catalog lock and its exact byte identity."""

    raw: bytes
    digest: str
    catalog_repository: str
    catalog_commit: str
    catalog_release: str
    templates_root: str
    index_path: str
    lifecycle_version: int
    core_repository: str
    core_commit: str
    core_release: str
    templates: Mapping[str, str]
    template_digests: Mapping[str, str]


def _require_string(data: dict[str, Any], field: str) -> str:
    value = data[field]
    if type(value) is not str or not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        _fail(f"{field} must be a non-empty control-free string")
    return value


def _validate_repository_url(value: str, field: str) -> None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        _fail(f"{field} must be an HTTPS GitHub repository URL", cause=exc)
    segments = parsed.path.removeprefix("/").split("/")
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(segments) != 2
        or not segments[1].endswith(".git")
        or not all(_REPOSITORY_SEGMENT_PATTERN.fullmatch(segment.removesuffix(".git")) for segment in segments)
    ):
        _fail(f"{field} must be an HTTPS GitHub repository URL")


def _validate_relative_path(value: str, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        _fail(f"{field} must be a safe repository-relative path")
    return path


def _validate_registry(value: Any) -> Mapping[str, str]:
    if type(value) is not dict or not value:
        _fail("templates must be a non-empty object")
    registry: dict[str, str] = {}
    folded: set[str] = set()
    for key, description in value.items():
        if type(key) is not str or _KEY_PATTERN.fullmatch(key) is None:
            _fail("template keys must be safe type/name identifiers")
        if any(
            segment.endswith((".", " ")) or segment.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
            for segment in key.split("/")
        ):
            _fail("template keys must be portable type/name identifiers")
        if key.casefold() in folded:
            _fail("template keys must be unique ignoring case")
        if type(description) is not str or not description:
            _fail("template descriptions must be non-empty strings")
        folded.add(key.casefold())
        registry[key] = description
    return MappingProxyType(registry)


def _validate_template_digests(value: Any, registry: Mapping[str, str]) -> Mapping[str, str]:
    if type(value) is not dict or value.keys() != registry.keys():
        _fail("template_digests keys must exactly match templates")
    digests: dict[str, str] = {}
    for key, digest in value.items():
        if type(digest) is not str or _DIGEST_PATTERN.fullmatch(digest) is None:
            _fail("template_digests values must be lowercase SHA-256 digests")
        digests[key] = digest
    return MappingProxyType(digests)


def parse_catalog_lock(raw: bytes) -> CatalogLock:
    """Validate *raw* as the schema-one lock without normalizing its digest."""
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("catalog lock must be valid UTF-8 JSON", cause=exc)
    if type(data) is not dict or data.keys() != _LOCK_FIELDS:
        _fail("catalog lock fields do not match schema version 1")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("schema_version must be integer 1")
    if type(data["lifecycle_version"]) is not int or data["lifecycle_version"] != 2:
        _fail("lifecycle_version must be integer 2")

    catalog_repository = _require_string(data, "catalog_repository")
    core_repository = _require_string(data, "core_repository")
    _validate_repository_url(catalog_repository, "catalog_repository")
    _validate_repository_url(core_repository, "core_repository")
    catalog_commit = _require_string(data, "catalog_commit")
    core_commit = _require_string(data, "core_commit")
    if _COMMIT_PATTERN.fullmatch(catalog_commit) is None:
        _fail("catalog_commit must be a full lowercase commit SHA")
    if _COMMIT_PATTERN.fullmatch(core_commit) is None:
        _fail("core_commit must be a full lowercase commit SHA")
    templates_root = _require_string(data, "templates_root")
    index_path = _require_string(data, "index_path")
    templates_root_path = _validate_relative_path(templates_root, "templates_root")
    index_path_value = _validate_relative_path(index_path, "index_path")
    try:
        index_path_value.relative_to(templates_root_path)
    except ValueError as exc:
        _fail("index_path must remain inside templates_root", cause=exc)

    templates = _validate_registry(data["templates"])
    return CatalogLock(
        raw=raw,
        digest=hashlib.sha256(raw).hexdigest(),
        catalog_repository=catalog_repository,
        catalog_commit=catalog_commit,
        catalog_release=_require_string(data, "catalog_release"),
        templates_root=templates_root,
        index_path=index_path,
        lifecycle_version=data["lifecycle_version"],
        core_repository=core_repository,
        core_commit=core_commit,
        core_release=_require_string(data, "core_release"),
        templates=templates,
        template_digests=_validate_template_digests(data["template_digests"], templates),
    )


def load_catalog_lock() -> CatalogLock:
    """Load and validate the raw lock bytes packaged in the AgentSeek wheel."""
    try:
        raw = files("agentseek").joinpath("data/catalog-lock.json").read_bytes()
    except OSError as exc:
        _fail("packaged catalog lock is unavailable", cause=exc)
    return parse_catalog_lock(raw)


def _path_lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _path_is_link_like(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    if stat.S_ISLNK(metadata.st_mode):
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None:
        try:
            if is_junction():
                return True
        except OSError:
            return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _ensure_cache_root(cache_root: Path) -> Path:
    try:
        if _path_is_link_like(cache_root):
            _fail("Cookiecutter cache directory must not be link-like")
        cache_root.mkdir(parents=True, exist_ok=True)
        if _path_is_link_like(cache_root):
            _fail("Cookiecutter cache directory must not be link-like")
        resolved = cache_root.resolve(strict=True)
    except CatalogError:
        raise
    except OSError as exc:
        _fail("Cookiecutter cache directory cannot be prepared", cause=exc)
    if not cache_root.is_dir() or resolved != cache_root.absolute():
        _fail("Cookiecutter cache directory is not controlled")
    return resolved


def _ensure_child_directory(parent: Path, name: str) -> Path:
    if not name or Path(name).name != name:
        _fail("cache directory name is invalid")
    child = parent / name
    if _path_is_link_like(child):
        _fail("cache directory must not be link-like")
    try:
        child.mkdir(exist_ok=True)
        if _path_is_link_like(child):
            _fail("cache directory must not be link-like")
        resolved = child.resolve(strict=True)
    except CatalogError:
        raise
    except OSError as exc:
        _fail("cache directory cannot be prepared", cause=exc)
    if not child.is_dir() or resolved.parent != parent or resolved != child:
        _fail("cache directory escaped its parent")
    return resolved


def _cache_layout(cache_root: Path, lock: CatalogLock, key: str) -> tuple[Path, Path, Path]:
    root = _ensure_cache_root(cache_root)
    namespace = _ensure_child_directory(root, _CACHE_NAMESPACE)
    coordinate = "\x00".join((lock.catalog_repository, lock.catalog_commit, lock.digest, key))
    # URL-safe Base64 retains the full SHA-256 identity in 43 filename-safe
    # characters, leaving room for the extracted template on Windows.
    coordinate_digest = urlsafe_b64encode(hashlib.sha256(coordinate.encode()).digest()).decode().rstrip("=")
    lock_dir = _ensure_child_directory(namespace, coordinate_digest)
    cache_entry = lock_dir / "template"
    lock_path = lock_dir / ".lock"
    if _path_is_link_like(cache_entry) or _path_is_link_like(lock_path):
        _fail("cache coordinate must not be link-like")
    return lock_dir, cache_entry, lock_path


def _expected_metadata(lock: CatalogLock, key: str) -> dict[str, object]:
    return {
        "schema_version": _CACHE_SCHEMA_VERSION,
        "catalog_repository": lock.catalog_repository,
        "catalog_commit": lock.catalog_commit,
        "template_key": key,
        "catalog_lock_sha256": lock.digest,
        "template_sha256": lock.template_digests[key],
    }


def _inspect_template_directory(directory: Path) -> tuple[list[Path], list[Path]]:
    if _path_is_link_like(directory):
        _fail("cached template contains link-like content")
    try:
        entries = list(os.scandir(directory))
    except OSError as exc:
        _fail("cached template cannot be inspected", cause=exc)
    directories: list[Path] = []
    regular_files: list[Path] = []
    for entry in entries:
        path = Path(entry.path)
        if _path_is_link_like(path):
            _fail("cached template contains link-like content")
        try:
            if entry.is_dir(follow_symlinks=False):
                directories.append(path)
            elif entry.is_file(follow_symlinks=False):
                regular_files.append(path)
            else:
                _fail("cached template contains unsupported content")
        except OSError as exc:
            _fail("cached template cannot be inspected", cause=exc)
    return directories, regular_files


def _template_entries(template_dir: Path) -> list[tuple[Path, bool]]:
    pending = [template_dir]
    entries: list[tuple[Path, bool]] = []
    while pending:
        directories, files_in_directory = _inspect_template_directory(pending.pop())
        pending.extend(directories)
        entries.extend((path, True) for path in directories)
        entries.extend((path, False) for path in files_in_directory)
    return entries


def _template_tree_digest(template_dir: Path) -> str:
    digest = hashlib.sha256()
    digest.update(b"agentseek-template-tree-v1\0")
    entries = sorted(
        _template_entries(template_dir),
        key=lambda item: item[0].relative_to(template_dir).as_posix(),
    )
    digest.update(len(entries).to_bytes(8, "big"))
    for path, is_directory in entries:
        try:
            relative = path.relative_to(template_dir).as_posix().encode("utf-8")
        except UnicodeEncodeError as exc:
            _fail("cached template path is not valid UTF-8", cause=exc)
        digest.update(b"d" if is_directory else b"f")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        if is_directory:
            continue
        descriptor: int | None = None
        try:
            descriptor = os.open(
                path,
                os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                _fail("cached template contains unsupported content")
            digest.update(b"x" if metadata.st_mode & 0o111 else b"-")
            digest.update(metadata.st_size.to_bytes(8, "big"))
            read_size = 0
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = None
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    read_size += len(chunk)
            if read_size != metadata.st_size:
                _fail("cached template changed while being read")
        except OSError as exc:
            _fail("cached template cannot be read", cause=exc)
        finally:
            if descriptor is not None:
                os.close(descriptor)
    return digest.hexdigest()


def _valid_template(template_dir: Path) -> bool:
    try:
        if _path_is_link_like(template_dir) or not template_dir.is_dir():
            return False
        context_path = template_dir / "cookiecutter.json"
        if _path_is_link_like(context_path) or not context_path.is_file():
            return False
        context = json.loads(context_path.read_text(encoding="utf-8"))
        project_root = template_dir / "{{cookiecutter.project_slug}}"
        if type(context) is not dict or "project_slug" not in context or not project_root.is_dir():
            return False
        if not any(path.is_file() for path in project_root.rglob("*")):
            return False
        _template_tree_digest(template_dir)
    except (CatalogError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return True


def _read_metadata(cache_entry: Path) -> dict[str, object] | None:
    path = cache_entry / _CACHE_METADATA
    if _path_is_link_like(path):
        return None
    try:
        metadata = path.lstat()
        cache_real = cache_entry.resolve(strict=True)
        if not stat.S_ISREG(metadata.st_mode) or path.resolve(strict=True).parent != cache_real:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if type(data) is dict else None


def _validated_cache(cache_entry: Path, lock: CatalogLock, key: str) -> Path | None:
    if _path_is_link_like(cache_entry) or not cache_entry.is_dir():
        return None
    try:
        cache_real = cache_entry.resolve(strict=True)
    except OSError:
        return None
    template_dir = cache_entry / lock.templates_root / key
    if not _valid_template(template_dir):
        return None
    try:
        template_real = template_dir.resolve(strict=True)
        if not _path_is_within(template_real, cache_real):
            return None
        tree_digest = _template_tree_digest(template_dir)
    except (CatalogError, OSError):
        return None
    if tree_digest != lock.template_digests[key]:
        return None
    expected = _expected_metadata(lock, key)
    actual = _read_metadata(cache_entry)
    if actual is None or actual.keys() != expected.keys() or actual != expected:
        return None
    if type(actual["schema_version"]) is not int:
        return None
    return template_dir


def _safe_archive_parts(name: str) -> tuple[str, ...]:
    if not name or "\\" in name or "//" in name or any(ord(char) < 32 or ord(char) == 127 for char in name):
        _fail("archive contains an unsafe path")
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    parts = tuple(part for part in posix.parts if part != "")
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or windows.root
        or not parts
        or any(part in {".", ".."} for part in parts)
        or any(
            part.endswith((".", " ")) or ":" in part or part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
            for part in parts
        )
    ):
        _fail("archive contains an unsafe path")
    return parts


def _write_member(archive: tarfile.TarFile, member: tarfile.TarInfo, destination: Path) -> None:
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            _fail("archive member content is unavailable")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        normalized_mode = 0o755 if member.mode & 0o111 else 0o644
        descriptor = os.open(destination, flags, normalized_mode)
        with os.fdopen(descriptor, "wb") as output:
            if hasattr(os, "fchmod"):
                os.fchmod(output.fileno(), normalized_mode)
            else:
                os.chmod(destination, normalized_mode)
            remaining = member.size
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    _fail("archive member is truncated")
                output.write(chunk)
                remaining -= len(chunk)
            if source.read(1):
                _fail("archive member exceeds its declared size")
    except CatalogError:
        raise
    except (OSError, tarfile.TarError) as exc:
        _fail("archive member could not be extracted", cause=exc)


@dataclass
class _ArchiveScan:
    root: str | None = None
    member_count: int = 0
    total_size: int = 0
    registry_bytes: bytes | None = None
    selected_files: int = 0
    seen: set[tuple[str, ...]] = field(default_factory=set)


def _validated_archive_member(member: tarfile.TarInfo, scan: _ArchiveScan) -> tuple[str, ...]:
    scan.member_count += 1
    if scan.member_count > MAX_ARCHIVE_MEMBERS:
        _fail("catalog archive exceeds the 10,000 member limit")
    _validate_declared_member_size(member.size)
    scan.total_size += member.size
    if scan.total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
        _fail("catalog archive exceeds the 256 MiB uncompressed limit")

    parts = _safe_archive_parts(member.name)
    if scan.root is None:
        scan.root = parts[0]
    elif parts[0] != scan.root:
        _fail("archive contains multiple repository roots")
    folded = tuple(part.casefold() for part in parts)
    if folded in scan.seen:
        _fail("archive contains duplicate paths")
    scan.seen.add(folded)
    if not (member.isdir() or member.isfile()):
        _fail("archive contains unsupported link or device content")
    return parts[1:]


def _read_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    source = archive.extractfile(member)
    if source is None:
        _fail("archive member content is unavailable")
    try:
        content = source.read(member.size + 1)
    except (OSError, tarfile.TarError) as exc:
        _fail("archive member content cannot be read", cause=exc)
    if len(content) != member.size:
        _fail("archive member is truncated or exceeds its declared size")
    return content


def _extract_selected_member(
    archive: tarfile.TarFile,
    member: tarfile.TarInfo,
    candidate: Path,
    lock: CatalogLock,
    key: str,
    tail: tuple[str, ...],
) -> int:
    destination = candidate.joinpath(lock.templates_root, key, *tail)
    if not tail:
        if member.isfile():
            _fail("selected template root must be a directory")
        destination.mkdir(parents=True, exist_ok=True)
        return 0
    if member.isdir():
        destination.mkdir(parents=True, exist_ok=True)
        return 0
    _write_member(archive, member, destination)
    return 1


def _decompress_archive(archive_path: Path, destination: Path) -> None:
    """Materialize a gzip archive while enforcing the expanded-stream budget.

    ``tarfile`` consumes PAX and GNU extension records before yielding the
    member they describe. Counting only yielded ``TarInfo`` objects therefore
    misses those records. Bounding the gzip stream first makes every expanded
    byte -- headers, extensions, padding, and file bodies -- part of the same
    limit before ``tarfile`` can allocate an extension payload.
    """
    if _path_lexists(destination) or _path_is_link_like(destination):
        _fail("catalog archive expansion destination is not empty")
    descriptor: int | None = None
    expanded = 0
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(destination, flags, 0o600)
        with (
            archive_path.open("rb") as source,
            gzip.GzipFile(fileobj=source, mode="rb") as compressed,
            os.fdopen(descriptor, "wb") as output,
        ):
            descriptor = None
            while chunk := compressed.read(min(1024 * 1024, MAX_TOTAL_UNCOMPRESSED_BYTES - expanded + 1)):
                expanded += len(chunk)
                if expanded > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    _fail("catalog archive exceeds the 256 MiB uncompressed limit")
                output.write(chunk)
    except CatalogError:
        raise
    except (EOFError, OSError, zlib.error) as exc:
        _fail("catalog archive is invalid or truncated", cause=exc)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _scan_template_archive(expanded_archive: Path, candidate: Path, lock: CatalogLock, key: str) -> _ArchiveScan:
    selected_relative = (*PurePosixPath(lock.templates_root).parts, *key.split("/"))
    index_relative = PurePosixPath(lock.index_path).parts
    scan = _ArchiveScan()
    with _BoundedTarFile.open(expanded_archive, mode="r:", tarinfo=_BoundedTarInfo) as archive:
        for member in archive:
            relative = _validated_archive_member(member, scan)
            if member.isfile() and relative == index_relative:
                scan.registry_bytes = _read_member(archive, member)
            if relative[: len(selected_relative)] != selected_relative:
                continue
            tail = relative[len(selected_relative) :]
            scan.selected_files += _extract_selected_member(archive, member, candidate, lock, key, tail)
    return scan


def _extract_template_archive(archive_path: Path, candidate: Path, lock: CatalogLock, key: str) -> Path:
    expanded_archive = archive_path.with_suffix("")
    try:
        _decompress_archive(archive_path, expanded_archive)
        scan = _scan_template_archive(expanded_archive, candidate, lock, key)
    except CatalogError:
        raise
    except (OSError, tarfile.TarError, EOFError) as exc:
        _fail("catalog archive is invalid or truncated", cause=exc)
    finally:
        if _path_lexists(expanded_archive):
            with suppress(OSError):
                expanded_archive.unlink()
    if scan.registry_bytes is None:
        _fail("archive is missing the catalog registry")
    try:
        registry = json.loads(scan.registry_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("archive registry is invalid", cause=exc)
    if registry != dict(lock.templates):
        _fail("archive registry does not match the embedded snapshot")
    template_dir = candidate / lock.templates_root / key
    if scan.selected_files == 0 or not _valid_template(template_dir):
        _fail("selected template is missing or incomplete")
    if _template_tree_digest(template_dir) != lock.template_digests[key]:
        _fail("selected template content does not match the embedded digest")
    return template_dir


def _write_metadata(cache_entry: Path, metadata: dict[str, object]) -> None:
    path = cache_entry / _CACHE_METADATA
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(metadata, stream, sort_keys=True)
    except OSError as exc:
        _fail("catalog metadata could not be written", cause=exc)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _move_stale_entry(cache_entry: Path, parent: Path) -> Path | None:
    if not _path_lexists(cache_entry):
        return None
    if _path_is_link_like(cache_entry):
        _fail("stale cache entry must not be link-like")
    # The coordinate lock serializes publishers, so a compact 64-bit suffix
    # is sufficient for stale-entry isolation and leaves Windows path headroom.
    stale = parent / f".s-{uuid.uuid4().hex[:16]}"
    if stale.parent != parent or _path_lexists(stale):
        _fail("stale cache destination is not confined")
    cache_entry.replace(stale)
    return stale


def _remove_stale_entry(stale: Path, parent: Path) -> None:
    if stale.parent != parent:
        _fail("stale cache entry escaped its coordinate")
    if not _path_lexists(stale):
        return
    if _path_is_link_like(stale):
        _fail("stale cache entry became link-like")
    try:
        if stat.S_ISDIR(stale.lstat().st_mode):
            shutil.rmtree(stale)
        else:
            stale.unlink()
    except OSError as exc:
        _fail("stale cache entry could not be removed", cause=exc)


def _archive_url(lock: CatalogLock) -> str:
    parsed = urlsplit(lock.catalog_repository)
    owner, repository = parsed.path.removeprefix("/").removesuffix(".git").split("/")
    return f"https://codeload.github.com/{owner}/{repository}/tar.gz/{lock.catalog_commit}"


def _validated_content_length(response: httpx.Response) -> None:
    content_encoding = response.headers.get("content-encoding")
    if content_encoding is not None and content_encoding.strip().casefold() != "identity":
        _fail("catalog archive response has an unsupported Content-Encoding")
    content_length = response.headers.get("content-length")
    if content_length is None:
        return
    try:
        declared = int(content_length)
    except ValueError:
        _fail("catalog archive has an invalid Content-Length")
    if declared < 0:
        _fail("catalog archive has an invalid Content-Length")
    if declared > MAX_COMPRESSED_BYTES:
        _fail("catalog archive exceeds the 64 MiB compressed limit")


def _write_response_body(response: httpx.Response, output: Any, deadline: float) -> int:
    downloaded = 0
    for chunk in response.iter_raw():
        if time.monotonic() > deadline:
            _fail("catalog archive download exceeded the overall timeout")
        downloaded += len(chunk)
        if downloaded > MAX_COMPRESSED_BYTES:
            _fail("catalog archive exceeds the 64 MiB compressed limit")
        output.write(chunk)
    return downloaded


def _download_archive(lock: CatalogLock, destination: Path) -> None:
    """Stream the exact-commit GitHub archive to one atomically visible file."""
    temporary = destination.parent / f".{destination.name}.download-{uuid.uuid4().hex}"
    if _path_lexists(destination) or _path_lexists(temporary) or _path_is_link_like(destination):
        _fail("catalog archive destination is not empty")
    descriptor: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600)
        deadline = time.monotonic() + _DOWNLOAD_OVERALL_TIMEOUT_SECONDS
        timeout = httpx.Timeout(
            connect=_DOWNLOAD_CONNECT_TIMEOUT_SECONDS,
            read=_DOWNLOAD_READ_TIMEOUT_SECONDS,
            write=_DOWNLOAD_READ_TIMEOUT_SECONDS,
            pool=_DOWNLOAD_CONNECT_TIMEOUT_SECONDS,
        )
        with os.fdopen(descriptor, "wb") as output:
            descriptor = None
            with httpx.stream(
                "GET",
                _archive_url(lock),
                headers={"Accept-Encoding": "identity"},
                timeout=timeout,
                follow_redirects=False,
            ) as response:
                response.raise_for_status()
                _validated_content_length(response)
                downloaded = _write_response_body(response, output, deadline)
        if time.monotonic() > deadline:
            _fail("catalog archive download exceeded the overall timeout")
        if downloaded == 0:
            _fail("catalog archive response was empty")
        temporary.replace(destination)
    except CatalogError:
        raise
    except (httpx.HTTPError, OSError) as exc:
        _fail("catalog archive download failed", cause=exc)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if _path_lexists(temporary):
            with suppress(OSError):
                temporary.unlink()


def _fetch_and_publish(namespace: Path, lock_dir: Path, cache_entry: Path, lock: CatalogLock, key: str) -> Path:
    # Staging below the compact namespace avoids adding the 64-character
    # coordinate hash to every extracted path on Windows.
    with tempfile.TemporaryDirectory(prefix=".catalog-", dir=namespace) as temporary:
        staging_directory = Path(temporary)
        if staging_directory.parent != namespace or _path_is_link_like(staging_directory):
            _fail("catalog staging directory escaped its coordinate")
        staging = staging_directory.resolve(strict=True)
        archive_path = staging / "catalog.tar.gz"
        _download_archive(lock, archive_path)
        candidate = staging / "candidate"
        candidate.mkdir()
        _extract_template_archive(archive_path, candidate, lock, key)
        _write_metadata(candidate, _expected_metadata(lock, key))
        stale = _move_stale_entry(cache_entry, lock_dir)
        try:
            if candidate.parent != staging or cache_entry.parent != lock_dir or _path_is_link_like(candidate):
                _fail("catalog publication destination is not confined")
            candidate.replace(cache_entry)
            if stale is not None:
                with suppress(CatalogError):
                    _remove_stale_entry(stale, lock_dir)
        except BaseException:
            if stale is not None and not _path_lexists(cache_entry):
                stale.replace(cache_entry)
            raise
    return cache_entry / lock.templates_root / key


def prepare_locked_template(lock: CatalogLock, key: str, cache_root: Path) -> Path:
    """Return one validated immutable template, downloading it only when needed."""
    if key not in lock.templates:
        _fail(f"template {key!r} is not present in the embedded registry")
    lock_dir, cache_entry, lock_path = _cache_layout(cache_root, lock, key)
    namespace = lock_dir.parent
    cached = _validated_cache(cache_entry, lock, key)
    if cached is not None:
        return cached
    try:
        with FileLock(lock_path, timeout=_CACHE_LOCK_TIMEOUT_SECONDS):
            if _path_is_link_like(lock_path) or lock_path.resolve(strict=True).parent != lock_dir:
                _fail("cache coordinate lock escaped its namespace")
            cached = _validated_cache(cache_entry, lock, key)
            if cached is not None:
                return cached
            return _fetch_and_publish(namespace, lock_dir, cache_entry, lock, key)
    except FileLockTimeout:
        cached = _validated_cache(cache_entry, lock, key)
        if cached is not None:
            return cached
        _fail("timed out waiting for the catalog cache lock")


__all__ = [
    "CatalogError",
    "CatalogLock",
    "load_catalog_lock",
    "parse_catalog_lock",
    "prepare_locked_template",
]
