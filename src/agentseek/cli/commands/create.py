"""``agentseek create`` — scaffold a new agent project from a cookiecutter template.

Named templates come from the standalone catalog recorded by the immutable lock
packaged in the AgentSeek wheel. Listing uses the lock's registry snapshot and
selected template content is cached by repository, commit, key, and lock digest.
Absolute local paths and external Cookiecutter URLs remain explicit development
paths and never participate in named default resolution.

Spec resolution:

* ``agentseek create``                                — interactive type + template selection.
* ``agentseek create bub``                            — ``templates/bub/default``.
* ``agentseek create bub/default``                    — ``templates/bub/default``.
* ``agentseek create bub --list-templates``           — list templates available for the type.
* ``agentseek create --list-templates --filter rag``  — list templates matching a keyword.
* ``agentseek create bub --template default``         — same as ``bub/default``.
* ``agentseek create bub --template``                 — list templates for the type (same as --list-templates).
* ``agentseek create --template``                     — list all templates across all types.
* ``agentseek create deepagents --output-dir /tmp``   — write the generated project under /tmp.
* ``agentseek create https://github.com/x/y.git``    — passthrough to cookiecutter.
* ``agentseek create /path/to/template``              — passthrough to cookiecutter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import tempfile
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any, Never
from urllib.parse import SplitResult, unquote, urlsplit, urlunsplit

import typer
from filelock import FileLock
from filelock import Timeout as FileLockTimeout
from typer.core import TyperGroup

from agentseek.cli import catalog as locked_catalog

# ---------------------------------------------------------------------------
# Typer plumbing
# ---------------------------------------------------------------------------


class _SwallowArgsGroup(TyperGroup):
    """Typer group that forwards every trailing token to the callback.

    Typer normally treats the first positional after the group name as a
    sub-command, so ``agentseek create deepagents --template default`` is
    rejected with "No such command 'deepagents'". We override
    ``parse_args`` to dump everything past the group's own options into
    ``ctx.args``, leaving callback-side argparse to interpret them.
    """

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        ctx.args = list(args)
        return []


app = typer.Typer(
    name="create",
    help="Scaffold a new agent project from a pre-built template.",
    add_completion=False,
    no_args_is_help=False,
    cls=_SwallowArgsGroup,
)

KNOWN_TYPES: tuple[str, ...] = ("bub", "deepagents", "langchain")
DEFAULT_TYPE = "bub"

_TEMPLATE_LIST_SENTINEL = "__list__"

# The canonical GitHub repo URL used when templates are not found locally.
REPO_URL = "https://github.com/ob-labs/agentseek"
REPO_GIT_URL = f"{REPO_URL}.git"
# The directory inside the repo that holds all cookiecutter templates.
TEMPLATES_DIR = "templates"
# Keep this name compact: the cache also contains a 64-character repository
# digest and a 40-character commit SHA, so long names can exceed MAX_PATH.
EXPLICIT_TEMPLATE_REPO_CACHE_DIR = ".as"
EXPLICIT_CATALOG_METADATA = ".agentseek-catalog-metadata.json"
EXPLICIT_CATALOG_REPOSITORY_DIR = "repository"
EXPLICIT_CATALOG_SCHEMA_VERSION = 1
EXPLICIT_CATALOG_LOCK_TIMEOUT_SECONDS = 30.0
EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS = 60.0
QUARANTINED_TEMPLATE_KEYS: frozenset[str] = frozenset({"bub/contextseek"})
_COMMIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_CHECKOUT_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,200}\Z")
_TEMPLATE_KEY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {"CON", "PRN", "AUX", "NUL"} | {f"COM{index}" for index in range(1, 10)} | {f"LPT{index}" for index in range(1, 10)}
)


# ---------------------------------------------------------------------------
# Template source resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemplateSource:
    """Resolved template location ready for ``cookiecutter()``."""

    template: str  # local path or remote URL
    directory: str | None = None  # cookiecutter ``directory`` kwarg (monorepo subdir)
    checkout: str | None = None  # cookiecutter ``checkout`` kwarg (branch / tag)
    install_source_path: PurePath | None = None  # local monorepo path for generated project deps
    install_source_url: str | None = None  # remote repo URL for generated project deps
    install_source_ref: str | None = None  # exact remote revision for generated project deps


@dataclass(frozen=True)
class _ExplicitCatalogCoordinate:
    fetch_url: str
    normalized_url: str
    commit: str


@dataclass(frozen=True)
class _PreparedCatalog:
    templates_root: Path | None
    registry: Mapping[str, str]
    source_policy: str
    catalog_lock: locked_catalog.CatalogLock | None = None

    @property
    def is_explicit(self) -> bool:
        return self.source_policy in {"explicit", "checkout-override"}

    @property
    def is_locked(self) -> bool:
        return self.source_policy in {"locked-index", "locked-template", "checkout-override"}


class _InvalidExplicitCatalog(ValueError):
    """Raised when an explicit catalog does not satisfy the public contract."""


def _git_toplevel() -> Path | None:
    """Return the repository root if we are inside a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


def _local_templates_root() -> Path | None:
    """Return ``<repo-root>/templates`` if it exists on disk.

    Resolution strategy (in order):

    1. Walk up from *this* source file looking for a ``templates/`` directory
       that contains at least one ``cookiecutter.json``.  This works regardless
       of the user's cwd, which is important because the user will typically
       ``cd`` into their desired output directory before running ``create``.
    2. Fall back to ``git rev-parse --show-toplevel`` (covers unusual layouts).
    """
    # Strategy 1: relative to source file.
    anchor: Path | None = Path(__file__).resolve().parent
    while anchor and anchor != anchor.parent:
        candidate = anchor / TEMPLATES_DIR
        if candidate.is_dir() and any(candidate.rglob("cookiecutter.json")):
            return candidate
        anchor = anchor.parent

    # Strategy 2: git toplevel.
    repo = _git_toplevel()
    if repo is not None:
        candidate = repo / TEMPLATES_DIR
        if candidate.is_dir():
            return candidate

    return None


def _resolve_type_template(
    project_type: str,
    template_name: str,
    *,
    catalog: _PreparedCatalog | None = None,
    templates_root: Path | None = None,
) -> TemplateSource:
    """Resolve ``<type>/<name>`` from an already prepared template root."""
    if catalog is None:
        if templates_root is None:
            raise TypeError
        catalog = _catalog_from_root(templates_root)
    if catalog.templates_root is None:
        raise TypeError
    template_path = catalog.templates_root / project_type / template_name
    if _catalog_has_template(catalog, project_type, template_name) and (template_path / "cookiecutter.json").is_file():
        install_source_path = catalog.templates_root.parent if catalog.source_policy == "local-core" else None
        return TemplateSource(
            template=str(template_path),
            install_source_path=install_source_path,
            install_source_url=(
                None
                if install_source_path
                else catalog.catalog_lock.core_repository
                if catalog.catalog_lock is not None
                else REPO_GIT_URL
            ),
            install_source_ref=catalog.catalog_lock.core_commit if catalog.catalog_lock is not None else None,
        )
    _print_unknown_template(project_type, template_name, catalog=catalog)
    raise typer.Exit(2)


def _template_key(project_type: str, template_name: str) -> str:
    return f"{project_type}/{template_name}"


def _is_quarantined_template(project_type: str, template_name: str) -> bool:
    return _template_key(project_type, template_name) in QUARANTINED_TEMPLATE_KEYS


def _is_external_spec(spec: str) -> bool:
    """Return ``True`` if *spec* looks like a URL or absolute local path."""
    windows_path = PureWindowsPath(spec)
    return (
        spec.startswith(("https://", "http://", "git@", "gh:"))
        or PurePosixPath(spec).is_absolute()
        or bool(windows_path.drive or windows_path.root)
    )


# ---------------------------------------------------------------------------
# Template listing / discovery
# ---------------------------------------------------------------------------


def _list_templates(
    project_type: str,
    catalog_or_root: _PreparedCatalog | Path | None = None,
) -> list[str]:
    """Return template names available under ``templates/<type>/``."""
    if catalog_or_root is None:
        templates_root = _local_templates_root()
        if templates_root is None:
            return []
        catalog = _catalog_from_root(templates_root)
    elif isinstance(catalog_or_root, _PreparedCatalog):
        catalog = catalog_or_root
    else:
        catalog = _catalog_from_root(catalog_or_root)
    if catalog.is_locked:
        prefix = f"{project_type}/"
        return sorted(key.removeprefix(prefix) for key in catalog.registry if key.startswith(prefix))
    if catalog.templates_root is None:
        return []
    type_dir = catalog.templates_root / project_type
    if not type_dir.is_dir():
        return []
    return sorted(
        entry.name
        for entry in type_dir.iterdir()
        if (entry / "cookiecutter.json").is_file() and _catalog_has_template(catalog, project_type, entry.name)
    )


def _normalize_explicit_repository_url(repository_url: str) -> str:
    """Return the credential-free HTTPS coordinate used only for cache identity."""
    if (
        not repository_url
        or "?" in repository_url
        or "#" in repository_url
        or any(ord(char) < 33 or char.isspace() for char in repository_url)
    ):
        raise ValueError
    try:
        parsed = urlsplit(repository_url)
        port = parsed.port
    except ValueError:
        raise ValueError from None
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or "@" in parsed.netloc
    ):
        raise ValueError

    decoded_path = parsed.path
    for _ in range(4):
        next_path = unquote(decoded_path)
        if next_path == decoded_path:
            break
        decoded_path = next_path
    else:
        raise ValueError
    if any(segment in {".", ".."} for segment in decoded_path.replace("\\", "/").split("/")):
        raise ValueError

    hostname = parsed.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    netloc = hostname if port in (None, 443) else f"{hostname}:{port}"
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    normalized = SplitResult("https", netloc, path, "", "")
    return urlunsplit(normalized)


def _explicit_catalog_coordinate(args: argparse.Namespace) -> _ExplicitCatalogCoordinate | None:
    repository_url = args.template_repo
    if repository_url is None:
        return None
    if args.spec and _is_external_spec(args.spec):
        typer.echo(
            "--template-repo cannot be combined with a positional URL or absolute path.",
            err=True,
        )
        raise typer.Exit(2)
    try:
        normalized_url = _normalize_explicit_repository_url(repository_url)
    except ValueError:
        typer.echo(
            "--template-repo must be an HTTPS repository URL without credentials, query, or fragment.",
            err=True,
        )
        raise typer.Exit(2) from None
    if args.checkout is None or _COMMIT_SHA_PATTERN.fullmatch(args.checkout) is None:
        typer.echo(
            "--checkout must be a 40-character lowercase commit SHA when --template-repo is used.",
            err=True,
        )
        raise typer.Exit(2)
    return _ExplicitCatalogCoordinate(
        fetch_url=repository_url,
        normalized_url=normalized_url,
        commit=args.checkout,
    )


def _git_head(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return result.stdout.strip()


def _git_templates_are_pristine(repo_root: Path) -> bool:
    """Return whether Git reports no tracked, untracked, or ignored template changes."""
    try:
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "git",
                "-C",
                str(repo_root),
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignored=matching",
                "--",
                TEMPLATES_DIR,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return result.stdout == ""


def _path_lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return True


def _path_is_link_like(path: Path) -> bool:
    """Detect POSIX links and Windows junction/reparse-point equivalents."""
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


def _explicit_catalog_metadata(coordinate: _ExplicitCatalogCoordinate) -> dict[str, object]:
    return {
        "schema_version": EXPLICIT_CATALOG_SCHEMA_VERSION,
        "repository_url": coordinate.normalized_url,
        "commit": coordinate.commit,
        "repository_subdirectory": TEMPLATES_DIR,
    }


def _read_explicit_catalog_metadata(cache_entry: Path) -> dict[str, object] | None:
    metadata_path = cache_entry / EXPLICIT_CATALOG_METADATA
    if _path_is_link_like(metadata_path):
        return None
    try:
        metadata_stat = metadata_path.lstat()
        metadata_real = metadata_path.resolve(strict=True)
        wrapper_real = cache_entry.resolve(strict=True)
        if not stat.S_ISREG(metadata_stat.st_mode) or metadata_real.parent != wrapper_real:
            return None
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_explicit_catalog_metadata(
    cache_entry: Path,
    coordinate: _ExplicitCatalogCoordinate,
) -> None:
    metadata_path = cache_entry / EXPLICIT_CATALOG_METADATA
    if _path_lexists(metadata_path) or _path_is_link_like(metadata_path):
        _reject_explicit_catalog("catalog metadata sidecar already exists or is link-like")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(metadata_path, flags, 0o600)
        metadata_stat = os.fstat(descriptor)
        if not stat.S_ISREG(metadata_stat.st_mode):
            _reject_explicit_catalog("catalog metadata sidecar must be a regular file")
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            json.dump(_explicit_catalog_metadata(coordinate), stream, sort_keys=True)
    except _InvalidExplicitCatalog:
        raise
    except OSError as exc:
        _reject_explicit_catalog("catalog metadata sidecar cannot be created safely", cause=exc)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _explicit_catalog_metadata_matches(
    actual: dict[str, object] | None,
    expected: dict[str, object],
) -> bool:
    if actual is None or actual.keys() != expected.keys():
        return False
    if type(actual["schema_version"]) is not int:
        return False
    if not all(type(actual[field]) is str for field in ("repository_url", "commit", "repository_subdirectory")):
        return False
    return actual == expected


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _reject_explicit_catalog(reason: str, *, cause: BaseException | None = None) -> Never:
    raise _InvalidExplicitCatalog(reason) from cause


def _explicit_templates_root(repo_root: Path) -> tuple[Path, Path]:
    if _path_is_link_like(repo_root):
        _reject_explicit_catalog("repository must not be link-like")
    try:
        repo_root = repo_root.resolve(strict=True)
        templates_root = repo_root / TEMPLATES_DIR
        if _path_is_link_like(templates_root):
            _reject_explicit_catalog(f"{TEMPLATES_DIR}/ must not be link-like")
        templates_real = templates_root.resolve(strict=True)
    except OSError as exc:
        _reject_explicit_catalog(f"missing {TEMPLATES_DIR}/ directory", cause=exc)
    if not templates_root.is_dir() or not _path_is_within(templates_real, repo_root):
        _reject_explicit_catalog(f"{TEMPLATES_DIR}/ must remain inside the repository")
    return templates_root, templates_real


def _load_strict_explicit_registry(templates_root: Path, templates_real: Path) -> dict[str, str]:
    index = templates_root / "index.json"
    if _path_is_link_like(index):
        _reject_explicit_catalog("templates/index.json must not be link-like")
    try:
        index_real = index.resolve(strict=True)
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _reject_explicit_catalog("templates/index.json must be valid UTF-8 JSON", cause=exc)
    if not _path_is_within(index_real, templates_real):
        _reject_explicit_catalog("templates/index.json must remain inside templates/")
    if not isinstance(data, dict) or not data:
        _reject_explicit_catalog("templates/index.json must be a non-empty object")
    if not all(isinstance(key, str) and _TEMPLATE_KEY_PATTERN.fullmatch(key) for key in data):
        _reject_explicit_catalog("registry keys must be safe type/name identifiers")
    if not all(isinstance(description, str) for description in data.values()):
        _reject_explicit_catalog("registry descriptions must be strings")
    casefold_keys: set[str] = set()
    for key in data:
        segments = key.split("/")
        if any(
            segment.endswith((".", " ")) or segment.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
            for segment in segments
        ):
            _reject_explicit_catalog("registry keys must use portable type/name identifiers")
        folded = key.casefold()
        if folded in casefold_keys:
            _reject_explicit_catalog("registry contains a case-insensitive duplicate key")
        casefold_keys.add(folded)
    return data


def _validate_explicit_template_symlinks(
    template_dir: Path,
    template_real: Path,
    key: str,
) -> None:
    pending = [template_dir]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            _reject_explicit_catalog(f"registered template {key} cannot be inspected", cause=exc)
        for entry in entries:
            path = Path(entry.path)
            if _path_is_link_like(path):
                _reject_explicit_catalog(f"registered template {key} contains a symlink or other link-like content")
            try:
                target = path.resolve(strict=True)
            except OSError as exc:
                _reject_explicit_catalog(f"registered template {key} contains unreadable content", cause=exc)
            if not _path_is_within(target, template_real):
                _reject_explicit_catalog(f"registered template {key} contains a path escape")
            try:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif not entry.is_file(follow_symlinks=False):
                    _reject_explicit_catalog(f"registered template {key} contains unsupported content")
            except OSError as exc:
                _reject_explicit_catalog(f"registered template {key} cannot be inspected", cause=exc)


def _validate_explicit_template(templates_root: Path, templates_real: Path, key: str) -> None:
    template_dir = templates_root / key
    if _path_is_link_like(template_dir):
        _reject_explicit_catalog(f"registered template {key} must not be link-like")
    try:
        template_real = template_dir.resolve(strict=True)
    except OSError as exc:
        _reject_explicit_catalog(f"registered template {key} is missing", cause=exc)
    if not template_dir.is_dir() or not _path_is_within(template_real, templates_real):
        _reject_explicit_catalog(f"registered template {key} escapes templates/")
    _validate_explicit_template_symlinks(template_dir, template_real, key)

    context = _load_cookiecutter_context(template_dir)
    if context is None or "project_slug" not in context:
        _reject_explicit_catalog(f"registered template {key} must contain valid cookiecutter.json with project_slug")
    project_root = template_dir / "{{cookiecutter.project_slug}}"
    if _path_is_link_like(project_root) or not project_root.is_dir():
        _reject_explicit_catalog(f"registered template {key} has no generated-project body")
    try:
        has_body = any(path.is_file() for path in project_root.rglob("*"))
    except OSError as exc:
        _reject_explicit_catalog(f"registered template {key} body cannot be inspected", cause=exc)
    if not has_body:
        _reject_explicit_catalog(f"registered template {key} has an empty generated-project body")


def _strict_explicit_catalog_descriptions(repo_root: Path) -> dict[str, str]:
    templates_root, templates_real = _explicit_templates_root(repo_root)
    data = _load_strict_explicit_registry(templates_root, templates_real)
    for key in data:
        _validate_explicit_template(templates_root, templates_real, key)
    return data


def _prepared_catalog(
    templates_root: Path | None,
    registry: Mapping[str, str],
    *,
    source_policy: str,
    catalog_lock: locked_catalog.CatalogLock | None = None,
) -> _PreparedCatalog:
    return _PreparedCatalog(
        templates_root=templates_root,
        registry=MappingProxyType(dict(registry)),
        source_policy=source_policy,
        catalog_lock=catalog_lock,
    )


def _validated_explicit_catalog_cache(
    cache_entry: Path,
    coordinate: _ExplicitCatalogCoordinate,
) -> _PreparedCatalog | None:
    if _path_is_link_like(cache_entry) or not cache_entry.is_dir():
        return None
    try:
        wrapper_real = cache_entry.resolve(strict=True)
    except OSError:
        return None
    if not _explicit_catalog_metadata_matches(
        _read_explicit_catalog_metadata(cache_entry),
        _explicit_catalog_metadata(coordinate),
    ):
        return None
    repo_root = cache_entry / EXPLICIT_CATALOG_REPOSITORY_DIR
    if _path_is_link_like(repo_root) or not repo_root.is_dir():
        return None
    try:
        if repo_root.resolve(strict=True).parent != wrapper_real:
            return None
    except OSError:
        return None
    if _git_head(repo_root) != coordinate.commit:
        return None
    if not _git_templates_are_pristine(repo_root):
        return None
    try:
        registry = _strict_explicit_catalog_descriptions(repo_root)
    except _InvalidExplicitCatalog:
        return None
    return _prepared_catalog(repo_root / TEMPLATES_DIR, registry, source_policy="explicit")


def _ensure_controlled_cache_directory(parent: Path, name: str) -> Path:
    directory = parent / name
    if _path_is_link_like(directory):
        _reject_explicit_catalog(f"cache directory {name} must not be link-like")
    try:
        directory.mkdir(exist_ok=True)
        if _path_is_link_like(directory):
            _reject_explicit_catalog(f"cache directory {name} must not be link-like")
        resolved = directory.resolve(strict=True)
    except OSError as exc:
        _reject_explicit_catalog(f"cache directory {name} cannot be prepared", cause=exc)
    if not directory.is_dir() or resolved.parent != parent or resolved != directory:
        _reject_explicit_catalog(f"cache directory {name} escaped its parent")
    return resolved


def _explicit_catalog_cache_layout(
    cookiecutters_dir: Path,
    coordinate: _ExplicitCatalogCoordinate,
) -> tuple[Path, Path, Path, Path]:
    try:
        if _path_is_link_like(cookiecutters_dir):
            _reject_explicit_catalog("Cookiecutter cache directory must not be link-like")
        cookiecutters_dir.mkdir(parents=True, exist_ok=True)
        if _path_is_link_like(cookiecutters_dir):
            _reject_explicit_catalog("Cookiecutter cache directory must not be link-like")
        cookiecutters_root = cookiecutters_dir.resolve(strict=True)
    except OSError as exc:
        _reject_explicit_catalog("Cookiecutter cache directory cannot be prepared", cause=exc)
    namespace = _ensure_controlled_cache_directory(cookiecutters_root, EXPLICIT_TEMPLATE_REPO_CACHE_DIR)
    repository_digest = hashlib.sha256(coordinate.normalized_url.encode()).hexdigest()
    digest_dir = _ensure_controlled_cache_directory(namespace, repository_digest)
    cache_entry = digest_dir / coordinate.commit
    lock_path = digest_dir / f".{coordinate.commit}.lock"
    if _path_is_link_like(cache_entry):
        _reject_explicit_catalog("cache commit entry must not be link-like")
    if _path_is_link_like(lock_path):
        _reject_explicit_catalog("cache coordinate lock must not be link-like")
    return namespace, digest_dir, cache_entry, lock_path


def _move_stale_cache_entry(cache_entry: Path, digest_dir: Path) -> Path | None:
    if not _path_lexists(cache_entry):
        return None
    if _path_is_link_like(cache_entry):
        _reject_explicit_catalog("stale cache entry must not be link-like")
    stale_entry = digest_dir / f".{cache_entry.name}.stale-{uuid.uuid4().hex}"
    if stale_entry.parent != digest_dir or _path_lexists(stale_entry) or _path_is_link_like(stale_entry):
        _reject_explicit_catalog("stale cache destination is not confined")
    cache_entry.replace(stale_entry)
    return stale_entry


def _validate_fetched_explicit_catalog(
    cloned_root: Path,
    staging_root: Path,
    coordinate: _ExplicitCatalogCoordinate,
) -> dict[str, str]:
    if not _path_is_within(cloned_root, staging_root):
        _reject_explicit_catalog("fetched repository escaped the staging directory")
    if _path_is_link_like(cloned_root):
        _reject_explicit_catalog("fetched repository must not be link-like")
    if _git_head(cloned_root) != coordinate.commit:
        _reject_explicit_catalog("fetched repository HEAD does not match --checkout")
    if not _git_templates_are_pristine(cloned_root):
        _reject_explicit_catalog("fetched repository templates are not pristine")
    return _strict_explicit_catalog_descriptions(cloned_root)


def _clone_explicit_repository(
    repository_url: str,
    checkout: str,
    destination: Path,
) -> None:
    """Clone one immutable catalog into the caller's exact controlled child."""
    git_environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        parent_real = destination.parent.resolve(strict=True)
    except OSError as exc:
        _reject_explicit_catalog("catalog staging parent is unavailable", cause=exc)
    if _path_lexists(destination) or _path_is_link_like(destination):
        _reject_explicit_catalog("catalog repository destination already exists or is link-like")
    try:
        subprocess.run(  # noqa: S603
            ["git", "clone", "--no-checkout", "--", repository_url, str(destination)],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
            env=git_environment,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        _reject_explicit_catalog("catalog repository fetch failed", cause=exc)
    try:
        if (
            _path_is_link_like(destination)
            or not destination.is_dir()
            or destination.resolve(strict=True).parent != parent_real
        ):
            _reject_explicit_catalog("catalog repository destination is not confined")
        subprocess.run(  # noqa: S603
            ["git", "-C", str(destination), "checkout", "--detach", checkout],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
            env=git_environment,
        )
    except _InvalidExplicitCatalog:
        raise
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        _reject_explicit_catalog("catalog repository checkout failed", cause=exc)
    if _git_head(destination) != checkout:
        _reject_explicit_catalog("fetched repository HEAD does not match --checkout")


def _fetch_and_publish_explicit_catalog(
    namespace: Path,
    digest_dir: Path,
    cache_entry: Path,
    coordinate: _ExplicitCatalogCoordinate,
) -> _PreparedCatalog:
    # Keep the staging tree directly below the controlled namespace rather
    # than below the digest and commit path. The latter exceeds Windows
    # MAX_PATH for otherwise valid Cookiecutter cache locations.
    with tempfile.TemporaryDirectory(prefix=".catalog-", dir=namespace) as temporary:
        staging_directory = Path(temporary)
        if staging_directory.parent != namespace or _path_is_link_like(staging_directory):
            _reject_explicit_catalog("catalog staging directory escaped its coordinate")
        staging_root = staging_directory.resolve(strict=True)
        candidate = _ensure_controlled_cache_directory(staging_root, "candidate")
        cloned_root = candidate / EXPLICIT_CATALOG_REPOSITORY_DIR
        _clone_explicit_repository(coordinate.fetch_url, coordinate.commit, cloned_root)
        cloned_root = cloned_root.resolve(strict=True)
        registry = _validate_fetched_explicit_catalog(cloned_root, staging_root, coordinate)
        _write_explicit_catalog_metadata(candidate, coordinate)
        stale_entry = _move_stale_cache_entry(cache_entry, digest_dir)
        try:
            if (
                cloned_root.parent != candidate
                or candidate.parent != staging_root
                or cache_entry.parent != digest_dir
                or _path_is_link_like(candidate)
            ):
                _reject_explicit_catalog("catalog publication destination is not confined")
            candidate.replace(cache_entry)
        except BaseException:
            if stale_entry is not None and not _path_lexists(cache_entry):
                stale_entry.replace(cache_entry)
            raise
    return _prepared_catalog(
        cache_entry / EXPLICIT_CATALOG_REPOSITORY_DIR / TEMPLATES_DIR,
        registry,
        source_policy="explicit",
    )


def _prepare_explicit_catalog(coordinate: _ExplicitCatalogCoordinate) -> _PreparedCatalog:
    from cookiecutter.config import get_user_config

    cookiecutters_dir = Path(get_user_config()["cookiecutters_dir"]).expanduser()
    try:
        namespace, digest_dir, cache_entry, lock_path = _explicit_catalog_cache_layout(
            cookiecutters_dir,
            coordinate,
        )
        prepared = _validated_explicit_catalog_cache(cache_entry, coordinate)
        if prepared is not None:
            return prepared

        try:
            lock = FileLock(lock_path, timeout=EXPLICIT_CATALOG_LOCK_TIMEOUT_SECONDS)
            with lock:
                if (
                    _path_is_link_like(namespace)
                    or namespace.resolve(strict=True) != namespace
                    or _path_is_link_like(digest_dir)
                    or digest_dir.resolve(strict=True) != digest_dir
                    or digest_dir.parent != namespace
                    or _path_is_link_like(lock_path)
                    or lock_path.resolve(strict=True).parent != digest_dir
                ):
                    _reject_explicit_catalog("cache coordinate lock escaped its namespace")
                if _path_is_link_like(cache_entry):
                    _reject_explicit_catalog("cache commit entry must not be link-like")
                prepared = _validated_explicit_catalog_cache(cache_entry, coordinate)
                if prepared is not None:
                    return prepared
                return _fetch_and_publish_explicit_catalog(
                    namespace,
                    digest_dir,
                    cache_entry,
                    coordinate,
                )
        except FileLockTimeout:
            prepared = _validated_explicit_catalog_cache(cache_entry, coordinate)
            if prepared is not None:
                return prepared
            raise
    except _InvalidExplicitCatalog as exc:
        typer.echo(f"Explicit template catalog is invalid: {exc}.", err=True)
        raise typer.Exit(1) from None
    except Exception:
        typer.echo("Could not prepare the explicit template catalog.", err=True)
        raise typer.Exit(1) from None


def _load_template_descriptions(templates_root: Path | None = None) -> dict[str, str]:
    if templates_root is None:
        templates_root = _local_templates_root()
    if templates_root is None:
        return {}
    index = templates_root / "index.json"
    if not index.is_file():
        return {}
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _catalog_from_root(
    templates_root: Path,
    *,
    source_policy: str | None = None,
) -> _PreparedCatalog:
    if source_policy is None:
        local_root = _local_templates_root()
        source_policy = "local-core" if local_root == templates_root else "remote-core"
    return _prepared_catalog(
        templates_root,
        _load_template_descriptions(templates_root),
        source_policy=source_policy,
    )


def _prepare_default_catalog(checkout: str | None = None) -> _PreparedCatalog:
    if checkout is not None:
        return _prepare_checkout_catalog(checkout)
    try:
        catalog_lock = locked_catalog.load_catalog_lock()
    except locked_catalog.CatalogError as exc:
        typer.echo(f"Could not load the locked template catalog: {exc}.", err=True)
        raise typer.Exit(1) from None
    return _prepared_catalog(
        None,
        catalog_lock.templates,
        source_policy="locked-index",
        catalog_lock=catalog_lock,
    )


def _validate_checkout_ref(ref: str) -> None:
    parts = ref.split("/")
    if (
        _CHECKOUT_REF_PATTERN.fullmatch(ref) is None
        or ".." in ref
        or "//" in ref
        or "@{" in ref
        or ref.endswith(("/", "."))
        or any(part in {"", ".", ".."} or part.startswith(".") or part.casefold().endswith(".lock") for part in parts)
    ):
        _reject_explicit_catalog("--checkout is not a safe Git branch or tag name")


def _resolve_standalone_catalog_ref(repository_url: str, ref: str) -> str:
    """Resolve one unambiguous standalone-catalog branch or tag to a commit."""
    if _COMMIT_SHA_PATTERN.fullmatch(ref) is not None:
        return ref
    _validate_checkout_ref(ref)
    command = [
        "git",
        "ls-remote",
        "--exit-code",
        "--",
        repository_url,
        f"refs/heads/{ref}",
        f"refs/tags/{ref}",
        f"refs/tags/{ref}^{{}}",
    ]
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
            env=environment,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        _reject_explicit_catalog("standalone catalog checkout ref could not be resolved", cause=exc)

    entries: dict[str, set[str]] = {}
    for line in result.stdout.splitlines():
        try:
            commit, remote_ref = line.split("\t", 1)
        except ValueError:
            _reject_explicit_catalog("standalone catalog checkout returned malformed Git output")
        if _COMMIT_SHA_PATTERN.fullmatch(commit) is None:
            _reject_explicit_catalog("standalone catalog checkout returned an invalid commit")
        entries.setdefault(remote_ref, set()).add(commit)

    heads = entries.get(f"refs/heads/{ref}", set())
    direct_tags = entries.get(f"refs/tags/{ref}", set())
    peeled_tags = entries.get(f"refs/tags/{ref}^{{}}", set())
    tags = peeled_tags or direct_tags
    if heads and tags:
        _reject_explicit_catalog("standalone catalog checkout ref is ambiguous between a branch and tag")
    commits = heads or tags
    if len(commits) != 1:
        _reject_explicit_catalog("standalone catalog checkout ref did not resolve to one commit")
    return next(iter(commits))


def _prepare_checkout_catalog(checkout: str) -> _PreparedCatalog:
    try:
        catalog_lock = locked_catalog.load_catalog_lock()
    except locked_catalog.CatalogError as exc:
        typer.echo(f"Could not load the locked template catalog: {exc}.", err=True)
        raise typer.Exit(1) from None
    try:
        commit = _resolve_standalone_catalog_ref(catalog_lock.catalog_repository, checkout)
        normalized = _normalize_explicit_repository_url(catalog_lock.catalog_repository)
    except (ValueError, _InvalidExplicitCatalog) as exc:
        typer.echo(f"Standalone template checkout is invalid: {exc}.", err=True)
        raise typer.Exit(1) from None
    prepared = _prepare_explicit_catalog(
        _ExplicitCatalogCoordinate(
            fetch_url=catalog_lock.catalog_repository,
            normalized_url=normalized,
            commit=commit,
        )
    )
    return _prepared_catalog(
        prepared.templates_root,
        prepared.registry,
        source_policy="checkout-override",
        catalog_lock=catalog_lock,
    )


def _prepare_locked_template_catalog(catalog: _PreparedCatalog, key: str) -> _PreparedCatalog:
    catalog_lock = catalog.catalog_lock
    if catalog_lock is None or not catalog.is_locked:
        return catalog
    from cookiecutter.config import get_user_config

    try:
        cookiecutters_dir = Path(get_user_config()["cookiecutters_dir"]).expanduser().absolute()
        template_dir = locked_catalog.prepare_locked_template(catalog_lock, key, cookiecutters_dir)
    except locked_catalog.CatalogError as exc:
        typer.echo(f"Could not prepare the locked template catalog: {exc}.", err=True)
        raise typer.Exit(1) from None
    except Exception:
        typer.echo("Could not prepare the locked template catalog.", err=True)
        raise typer.Exit(1) from None
    return _prepared_catalog(
        template_dir.parents[1],
        catalog.registry,
        source_policy="locked-template",
        catalog_lock=catalog_lock,
    )


def _catalog_has_template(
    catalog: _PreparedCatalog,
    project_type: str,
    template_name: str,
) -> bool:
    if not catalog.is_explicit and _is_quarantined_template(project_type, template_name):
        return False
    if not catalog.registry and not catalog.is_explicit:
        return True
    return _template_key(project_type, template_name) in catalog.registry


def _terminal_safe(value: str) -> str:
    """Escape terminal control characters while keeping printable Unicode intact."""
    escaped: list[str] = []
    for char in value:
        codepoint = ord(char)
        escaped.append(f"\\x{codepoint:02x}" if codepoint < 32 or 0x7F <= codepoint < 0xA0 else char)
    return "".join(escaped)


def _print_templates_table(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str] | None = None,
    *,
    filter_keyword: str | None = None,
) -> None:
    if not templates:
        if filter_keyword:
            typer.echo(f"No templates matched filter {filter_keyword!r} for type {project_type!r}.")
            return
        typer.echo(f"No templates found for type {project_type!r}.")
        return
    if descriptions is None:
        descriptions = _load_template_descriptions()
    typer.echo(f"\n  {project_type} ({len(templates)} templates)")
    typer.echo(f"  {'─' * 60}")
    for name in templates:
        key = f"{project_type}/{name}"
        desc = descriptions.get(key, "")
        typer.echo(f"    {key}")
        if desc:
            typer.echo(f"      {_terminal_safe(desc)}")


def _template_matches_filter(project_type: str, template_name: str, descriptions: dict[str, str], keyword: str) -> bool:
    key = _template_key(project_type, template_name)
    haystack = f"{key}\n{descriptions.get(key, '')}".casefold()
    return keyword.casefold() in haystack


def _filter_templates(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str],
    filter_keyword: str | None,
) -> list[str]:
    if not filter_keyword:
        return templates
    return [name for name in templates if _template_matches_filter(project_type, name, descriptions, filter_keyword)]


def _print_all_templates(
    catalog: _PreparedCatalog,
    *,
    filter_keyword: str | None = None,
) -> None:
    """Print all templates across all types with usage hints."""
    descriptions = dict(catalog.registry)
    total = 0
    for project_type in KNOWN_TYPES:
        templates = _filter_templates(
            project_type,
            _list_templates(project_type, catalog),
            descriptions,
            filter_keyword,
        )
        total += len(templates)
        if templates or filter_keyword is None:
            _print_templates_table(project_type, templates, descriptions)
    if filter_keyword and not total:
        typer.echo(f"No templates matched filter {filter_keyword!r}.")
        return
    if total:
        typer.echo("\n  Usage:")
        if filter_keyword:
            typer.echo("    agentseek create <type>/<name>")
        else:
            typer.echo("    agentseek create <type>/<name>       e.g. agentseek create bub/default")
        typer.echo("    agentseek create <type>              use default template for the type")
        typer.echo("    agentseek create                     interactive selection")
        typer.echo()


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------


def _prompt_project_type() -> str:
    typer.echo("Select an agent framework type:")
    for index, name in enumerate(KNOWN_TYPES, start=1):
        marker = " (default)" if name == DEFAULT_TYPE else ""
        typer.echo(f"  {index}. {name}{marker}")
    raw = typer.prompt(
        f"Choose [1-{len(KNOWN_TYPES)}]",
        default=str(KNOWN_TYPES.index(DEFAULT_TYPE) + 1),
    )
    return _coerce_type_choice(raw)


def _coerce_type_choice(raw: str) -> str:
    cleaned = raw.strip().lower()
    if cleaned in KNOWN_TYPES:
        return cleaned
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(KNOWN_TYPES):
            return KNOWN_TYPES[index]
    msg = f"Invalid choice {raw!r}. Expected a number 1-{len(KNOWN_TYPES)} or one of: {', '.join(KNOWN_TYPES)}."
    raise typer.BadParameter(msg)


def _prompt_template_name(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str] | None = None,
) -> str:
    if len(templates) == 1:
        return templates[0]
    if descriptions is None:
        descriptions = _load_template_descriptions()
    typer.echo(f"Available {project_type} templates:")
    width = max(len(name) for name in templates)
    for index, name in enumerate(templates, start=1):
        desc = descriptions.get(f"{project_type}/{name}", "")
        suffix = f"  — {_terminal_safe(desc)}" if desc else ""
        typer.echo(f"  {index}. {name:<{width}}{suffix}")
    raw = typer.prompt(f"Choose template [1-{len(templates)}]", default="1")
    cleaned = raw.strip()
    if cleaned in templates:
        return cleaned
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(templates):
            return templates[index]
    msg = f"Invalid choice {raw!r}."
    raise typer.BadParameter(msg)


# ---------------------------------------------------------------------------
# Cookiecutter invocation
# ---------------------------------------------------------------------------


def _cookiecutter_source_context(source: TemplateSource) -> dict[str, str]:
    """Build safe local-source values for structured template files."""
    install_source_path = source.install_source_path
    source_path = str(install_source_path) if install_source_path is not None else ""
    source_path_posix = install_source_path.as_posix() if install_source_path is not None else ""
    context = {
        "_agentseek_source_path": source_path,
        "_agentseek_source_path_posix": source_path_posix,
        "_agentseek_source_path_shell": shlex.quote(source_path_posix) if source_path_posix else "",
        "_agentseek_source_url": source.install_source_url or REPO_GIT_URL,
    }
    if source.install_source_ref is not None:
        context["_agentseek_source_ref"] = source.install_source_ref
    return context


def _run_cookiecutter(
    source: TemplateSource,
    *,
    output_dir: Path,
    no_input: bool,
) -> Path | None:
    """Invoke cookiecutter; isolated so tests can monkeypatch."""
    from cookiecutter.exceptions import OutputDirExistsException
    from cookiecutter.main import cookiecutter

    try:
        generated = cookiecutter(
            template=source.template,
            output_dir=str(output_dir),
            no_input=no_input,
            directory=source.directory,
            checkout=source.checkout,
            extra_context=_cookiecutter_source_context(source),
        )
        return Path(generated) if generated else None
    except OutputDirExistsException:
        typer.echo(
            "Target directory already exists. Remove it first or choose a different location.",
            err=True,
        )
        raise typer.Exit(1) from None


# ---------------------------------------------------------------------------
# Argparse CLI surface
# ---------------------------------------------------------------------------


def _parse_argv(argv: list[str]) -> argparse.Namespace:
    """Parse the raw create argv with argparse.

    Using argparse here (instead of additional Typer ``Option``s) keeps the
    documented ``agentseek create [SPEC] [--option ...]`` shape intact even
    though Typer would otherwise insist on a ``COMMAND`` after the positional.
    """
    parser = argparse.ArgumentParser(
        prog="agentseek create",
        add_help=True,
        description="Scaffold a new agent project from a pre-built template.",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help=(
            "Template spec. Can be a framework type (bub, deepagents, langchain), "
            "a type/name pair (bub/default), a git URL, or a local path."
        ),
    )
    parser.add_argument(
        "--template",
        nargs="?",
        default=None,
        const=_TEMPLATE_LIST_SENTINEL,
        help=(
            "Named template under the chosen type (e.g. --template default). "
            "Pass --template with no value to list available templates."
        ),
    )
    parser.add_argument(
        "--checkout",
        default=None,
        help="Branch, tag, or commit to checkout when fetching from a remote repository.",
    )
    parser.add_argument(
        "--template-repo",
        default=None,
        help=(
            "HTTPS AgentSeek catalog repository containing templates/index.json. "
            "Requires --checkout with a full 40-character lowercase commit SHA."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where the generated project should be written.",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List templates available for the chosen type and exit.",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="Keyword used to filter listed templates by spec or description.",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Skip cookiecutter prompts (use template defaults).",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help=(
            "Print template description and configuration without generating a project. "
            "Use with a spec like ``agentseek create bub/default --describe``."
        ),
    )
    return parser.parse_args(argv)


def _load_cookiecutter_context(template_dir: Path) -> dict[str, object] | None:
    """Load ``cookiecutter.json`` from *template_dir* if it exists."""
    cookiecutter_json = template_dir / "cookiecutter.json"
    if not cookiecutter_json.is_file():
        return None
    try:
        data = json.loads(cookiecutter_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _describe_template(
    source: TemplateSource,
    *,
    catalog: _PreparedCatalog,
) -> None:
    """Print template spec, description, and cookiecutter variables.

    Does **not** run cookiecutter or create any files.
    """
    template_dir = Path(source.template)

    # Build a clean key (e.g. "bub/default") from the templates root.
    if catalog.templates_root is None:
        spec_key = f"{template_dir.parent.name}/{template_dir.name}"
    else:
        try:
            rel = template_dir.relative_to(catalog.templates_root)
            parts = rel.parts
            spec_key = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else str(rel)
        except ValueError:
            spec_key = f"{template_dir.parent.name}/{template_dir.name}"

    description = catalog.registry.get(spec_key, "")

    typer.echo(f"\n  Template: {spec_key}")
    typer.echo(f"  {'─' * 60}")
    if description:
        typer.echo(f"  Description: {_terminal_safe(description)}")
    else:
        typer.echo("  Description: (none)")

    typer.echo(f"  Path: {template_dir}")

    context = _load_cookiecutter_context(template_dir)
    if context is None:
        typer.echo("  Cookiecutter variables: (none)")
        typer.echo()
        return

    typer.echo(f"  Cookiecutter variables ({len(context)}):")
    for key, value in context.items():
        display_key = _terminal_safe(str(key))
        display = _terminal_safe(value) if isinstance(value, str) else json.dumps(value)
        # Truncate long values for readability.
        if len(display) > 80:
            display = display[:77] + "..."
        typer.echo(f"    {display_key}: {display}")
    typer.echo()


def _handle_external_spec(args: argparse.Namespace) -> None:
    """Run cookiecutter for external specs unless describe mode is requested."""
    if args.describe:
        typer.echo(
            "--describe supports named AgentSeek catalog templates such as 'bub/default', "
            "not direct Cookiecutter sources.",
            err=True,
        )
        raise typer.Exit(2)

    source = TemplateSource(
        template=args.spec,
        directory=args.template,  # --template doubles as directory for external
        checkout=args.checkout,
    )
    output_dir = args.output_dir if args.output_dir is not None else Path.cwd()
    generated = _run_cookiecutter(source, output_dir=output_dir, no_input=args.no_input)
    _print_created_next_steps(generated, base_dir=Path.cwd())


# ---------------------------------------------------------------------------
# Main callback
# ---------------------------------------------------------------------------


def _catalog_for_request(
    args: argparse.Namespace,
    explicit_catalog: _ExplicitCatalogCoordinate | None,
) -> _PreparedCatalog:
    if explicit_catalog is not None:
        return _prepare_explicit_catalog(explicit_catalog)
    return _prepare_default_catalog(checkout=args.checkout)


def _choose_template_name(
    args: argparse.Namespace,
    catalog: _PreparedCatalog,
    project_type: str,
    template_name: str | None,
) -> str:
    selected = template_name if template_name is not None else args.template
    if selected is not None:
        return selected
    if args.no_input:
        return "default"
    descriptions = dict(catalog.registry)
    available = _list_templates(project_type, catalog)
    if not available:
        return "default"
    if len(available) == 1:
        return available[0]
    return _prompt_template_name(project_type, available, descriptions)


@app.callback(invoke_without_command=True)
def create(ctx: typer.Context) -> None:
    """Scaffold a new agent project from a pre-built template."""
    args = _parse_new_args(ctx)
    output_dir = args.output_dir if args.output_dir is not None else Path.cwd()
    explicit_catalog = _explicit_catalog_coordinate(args)

    # --- External spec (URL or absolute path) → passthrough to cookiecutter ---
    if args.spec and _is_external_spec(args.spec):
        _handle_external_spec(args)
        return

    # --- Parse spec into (type, name) ---
    project_type, template_name = _split_spec(args)

    # --- --list-templates or --template (no value) ---
    if args.list_templates or args.template == _TEMPLATE_LIST_SENTINEL:
        _validate_optional_project_type(project_type)
        catalog = _catalog_for_request(args, explicit_catalog)
        _show_templates(
            project_type,
            catalog=catalog,
            filter_keyword=args.filter,
        )
        return

    catalog = _catalog_for_request(args, explicit_catalog)

    # --- Interactive type selection if needed ---
    if project_type is None:
        project_type = _prompt_project_type()

    _validate_project_type(project_type)

    # --- Resolve template name ---
    template_name = _choose_template_name(args, catalog, project_type, template_name)

    if not _catalog_has_template(catalog, project_type, template_name):
        _print_unknown_template(project_type, template_name, catalog=catalog)
        raise typer.Exit(2)

    if catalog.source_policy == "locked-index":
        catalog = _prepare_locked_template_catalog(catalog, _template_key(project_type, template_name))

    source = _resolve_type_template(
        project_type,
        template_name,
        catalog=catalog,
    )

    # --- --describe: print template info without generating ---
    if args.describe:
        _describe_template(source, catalog=catalog)
        return

    generated = _run_cookiecutter(source, output_dir=output_dir, no_input=args.no_input)
    _print_created_next_steps(generated, base_dir=Path.cwd())


def _parse_new_args(ctx: typer.Context) -> argparse.Namespace:
    try:
        return _parse_argv(list(ctx.args))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        raise typer.Exit(code) from exc


def _split_spec(args: argparse.Namespace) -> tuple[str | None, str | None]:
    """Split the positional spec into ``(type, name)``.

    Returns ``(None, None)`` when no spec was given (interactive mode).
    """
    spec = args.spec
    if spec is None:
        return None, None
    # "bub/default" → ("bub", "default")
    if "/" in spec and not _is_external_spec(spec):
        parts = spec.split("/", 1)
        return parts[0], parts[1]
    # "bub" → ("bub", None) — name resolved later
    return spec, None


def _validate_project_type(project_type: str) -> None:
    if project_type not in KNOWN_TYPES:
        typer.echo(
            f"Unknown framework type {project_type!r}. Expected one of: {', '.join(KNOWN_TYPES)}.",
            err=True,
        )
        raise typer.Exit(2)


def _validate_optional_project_type(project_type: str | None) -> None:
    if project_type is not None:
        _validate_project_type(project_type)


def _print_unknown_template(
    project_type: str,
    template_name: str,
    *,
    catalog: _PreparedCatalog,
) -> None:
    available = _list_templates(project_type, catalog)
    typer.echo(f"Template {project_type}/{template_name} was not found. Supported templates:", err=True)
    _print_templates_table(project_type, available, dict(catalog.registry))


def _show_templates(
    project_type: str | None,
    *,
    catalog: _PreparedCatalog,
    filter_keyword: str | None = None,
) -> None:
    if project_type is not None:
        _validate_project_type(project_type)
    descriptions = dict(catalog.registry)
    if project_type is None:
        _print_all_templates(
            catalog,
            filter_keyword=filter_keyword,
        )
        return
    templates = _filter_templates(
        project_type,
        _list_templates(project_type, catalog),
        descriptions,
        filter_keyword,
    )
    _print_templates_table(project_type, templates, descriptions, filter_keyword=filter_keyword)
    typer.echo()


def _print_created_next_steps(generated: Path | None, *, base_dir: Path) -> None:
    if generated is None:
        return
    display_path = _display_generated_path(generated, base_dir=base_dir)
    typer.echo(f"Created {display_path}")
    typer.echo()
    typer.echo("Next (PowerShell):" if os.name == "nt" else "Next:")
    typer.echo(f"  {_directory_change_command(display_path)}")
    typer.echo("  agentseek info")
    typer.echo("  agentseek task --list")
    typer.echo("  agentseek doctor")


def _quote_directory_for_shell(path: str) -> str:
    if os.name == "nt":
        # cmd.exe expands %NAME% even inside double quotes. PowerShell single
        # quotes and -LiteralPath preserve valid Windows directory names.
        return "'" + path.replace("'", "''") + "'"
    return shlex.quote(path)


def _directory_change_command(path: str) -> str:
    """Return a copy-pasteable directory-change command for the supported shell."""

    command = "Set-Location -LiteralPath" if os.name == "nt" else "cd"
    return f"{command} {_quote_directory_for_shell(path)}"


def _display_generated_path(generated: Path, *, base_dir: Path) -> str:
    try:
        return str(generated.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(generated)


__all__ = ["DEFAULT_TYPE", "KNOWN_TYPES", "REPO_URL", "TemplateSource", "app"]
