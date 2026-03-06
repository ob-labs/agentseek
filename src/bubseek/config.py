"""Configuration and lockfile helpers for bubseek distribution."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

CONFIG_FILE_NAME = "bubseek.toml"
LOCK_FILE_NAME = "bubseek.lock"
SKILL_FILE_NAME = "SKILL.md"
DEFAULT_CONTRIB_PACKAGES = ("bub-codex", "bub-schedule")
DEFAULT_CONTRIB_REPO = "https://github.com/bubbuild/bub-contrib"
DEFAULT_BUB_PATH = "../.."
GIT_SOURCE_RE = re.compile(
    r"^git\+(?P<repo>[^@#]+?)(?:@(?P<ref>[^#]+))?(?:#subdirectory=(?P<subdirectory>.+))?$"
)
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
IGNORED_TREE_NAMES = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}


@dataclass(frozen=True)
class SourceEntry:
    kind: Literal["local", "remote"]
    name: str | None = None
    path: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class LockedSourceEntry:
    kind: Literal["local", "remote"]
    sha256: str
    name: str | None = None
    path: str | None = None
    source: str | None = None
    resolved_commit: str | None = None


BubEntry = SourceEntry
ContribEntry = SourceEntry
SkillEntry = SourceEntry
LockedBubEntry = LockedSourceEntry
LockedContribEntry = LockedSourceEntry
LockedSkillEntry = LockedSourceEntry


@dataclass(frozen=True)
class ResolvedGitSource:
    source: str
    resolved_commit: str


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    version: str


class SourceConfigItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str | None = Field(default=None, validation_alias=AliasChoices("path", "subdirectory"))
    repo: str | None = None
    ref: str | None = None
    source: str | None = None

    def to_entry(
        self,
        *,
        name: str | None = None,
        default_path: str | None = None,
        default_repo: str | None = None,
    ) -> SourceEntry:
        path = self.path or default_path
        if self.source is not None:
            return SourceEntry(name=name, kind="remote", source=self.source)

        repo = self.repo or default_repo
        if repo is not None:
            return SourceEntry(name=name, kind="remote", source=_git_source(repo=repo, subdirectory=path, ref=self.ref))

        if path is None:
            raise ValueError(f"source path missing: {name or 'entry'}")
        return SourceEntry(name=name, kind="local", path=path)


class BubConfigItem(SourceConfigItem):
    @model_validator(mode="after")
    def apply_defaults(self) -> BubConfigItem:
        if self.path is None and self.repo is None and self.source is None:
            self.path = DEFAULT_BUB_PATH
        return self

    def to_bub_entry(self) -> BubEntry:
        return self.to_entry()


class ContribConfigItem(SourceConfigItem):
    name: str

    @model_validator(mode="after")
    def apply_defaults(self) -> ContribConfigItem:
        if self.source is None and self.repo is None and self.path is None:
            self.repo = DEFAULT_CONTRIB_REPO
            self.path = f"packages/{self.name}"
        elif self.source is None and self.repo is not None and self.path is None:
            self.path = f"packages/{self.name}"
        return self

    def to_contrib_entry(self) -> ContribEntry:
        return self.to_entry(name=self.name)


class LegacyContribConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo: str = DEFAULT_CONTRIB_REPO
    ref: str | None = None
    packages: list[str] = Field(default_factory=list)

    def to_entries(self) -> list[ContribEntry]:
        return [
            SourceEntry(
                name=name,
                kind="remote",
                source=_git_source(repo=self.repo, subdirectory=f"packages/{name}", ref=self.ref),
            )
            for name in self.packages
            if name.strip()
        ]


class SkillConfigItem(SourceConfigItem):
    name: str | None = None
    path: str = Field(validation_alias=AliasChoices("path", "subdirectory"))

    def to_skill_entry(self) -> SkillEntry:
        name = self.name or Path(self.path).name
        return self.to_entry(name=name)


class LegacySkillsConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    paths: list[str] = Field(default_factory=list)

    def to_entries(self) -> list[SkillEntry]:
        return [SourceEntry(name=Path(path).name, kind="local", path=path) for path in self.paths if path.strip()]


class BubseekConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project: ProjectConfig
    bub: BubConfigItem = Field(default_factory=BubConfigItem)
    contrib: list[ContribConfigItem] | LegacyContribConfig = Field(default_factory=list)
    skills: list[SkillConfigItem] | LegacySkillsConfig = Field(default_factory=list)


class LockMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lock_version: int = 1
    config_file: str
    config_sha256: str


class LockedSourceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["local", "remote"] | None = None
    sha256: str
    path: str | None = None
    source: str | None = None
    resolved_commit: str | None = None

    @model_validator(mode="after")
    def validate_entry(self) -> LockedSourceRecord:
        inferred_kind = self.kind or _infer_locked_kind(path=self.path, source=self.source)
        if inferred_kind == "local":
            if self.path is None:
                raise ValueError("locked local path missing")
            self.kind = inferred_kind
            self.source = None
            self.resolved_commit = None
            return self

        if self.source is None:
            raise ValueError("locked remote source missing")
        self.kind = inferred_kind
        self.path = None
        self.resolved_commit = _validated_resolved_commit(source=self.source, resolved_commit=self.resolved_commit)
        return self

    def to_entry(self, *, name: str | None = None) -> LockedSourceEntry:
        if self.kind is None:
            raise ValueError("locked kind missing")
        return LockedSourceEntry(
            name=name,
            kind=self.kind,
            sha256=self.sha256,
            path=self.path,
            source=self.source,
            resolved_commit=self.resolved_commit,
        )


class LockedNamedSourceRecord(LockedSourceRecord):
    name: str

    def to_entry(self, *, name: str | None = None) -> LockedSourceEntry:
        if name is not None and name != self.name:
            raise ValueError(f"locked entry name mismatch: {self.name} != {name}")
        return super().to_entry(name=self.name)


LockedBubRecord = LockedSourceRecord
LockedContribRecord = LockedNamedSourceRecord
LockedSkillRecord = LockedNamedSourceRecord


class BubseekLock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    meta: LockMeta
    bub: LockedBubRecord | None = None
    contrib: list[LockedContribRecord] = Field(default_factory=list)
    skills: list[LockedSkillRecord] = Field(default_factory=list)


def distribution_root() -> Path:
    """Return the root directory of the bubseek distribution."""
    return Path(__file__).resolve().parents[2]


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve config path, defaulting to `<distribution_root>/bubseek.toml`."""
    if config_path is not None:
        return Path(config_path).expanduser().resolve()
    candidate = distribution_root() / CONFIG_FILE_NAME
    if not candidate.is_file():
        raise FileNotFoundError(f"config file not found: {candidate}")
    return candidate


def resolve_lock_path(lock_path: str | Path | None = None, *, config_path: Path | None = None) -> Path:
    """Resolve lock path with config-neighbor fallback."""
    if lock_path is not None:
        return Path(lock_path).expanduser().resolve()
    base = config_path if config_path is not None else resolve_config_path()
    return base.parent / LOCK_FILE_NAME


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load bubseek config from TOML file."""
    return load_config_model(config_path).model_dump(mode="python", exclude_none=True)


def load_config_model(config_path: str | Path | None = None) -> BubseekConfig:
    path = resolve_config_path(config_path)
    return BubseekConfig.model_validate(_load_toml(path))


def load_lock(lock_path: str | Path | None = None, *, config_path: str | Path | None = None) -> dict[str, Any]:
    """Load bubseek lock from TOML file."""
    return load_lock_model(lock_path, config_path=config_path).model_dump(mode="python", exclude_none=True)


def load_lock_model(lock_path: str | Path | None = None, *, config_path: str | Path | None = None) -> BubseekLock:
    resolved_config_path = resolve_config_path(config_path) if config_path is not None else None
    path = resolve_lock_path(lock_path, config_path=resolved_config_path)
    return BubseekLock.model_validate(_load_toml(path))


def configured_bub_entry(config: dict[str, Any] | BubseekConfig) -> BubEntry:
    config_model = _coerce_config_model(config)
    return config_model.bub.to_bub_entry()


def configured_contrib_entries(config: dict[str, Any] | BubseekConfig) -> list[ContribEntry]:
    """Read contrib entries from config, supporting legacy and multi-repo layouts."""
    config_model = _coerce_config_model(config)
    if isinstance(config_model.contrib, LegacyContribConfig):
        return config_model.contrib.to_entries()
    return [item.to_contrib_entry() for item in config_model.contrib]


def configured_skill_entries(config: dict[str, Any] | BubseekConfig) -> list[SkillEntry]:
    """Read skill entries from config, supporting local and remote repositories."""
    config_model = _coerce_config_model(config)
    if isinstance(config_model.skills, LegacySkillsConfig):
        return config_model.skills.to_entries()
    return [item.to_skill_entry() for item in config_model.skills]


def locked_bub_entry(lock: dict[str, Any] | BubseekLock) -> LockedBubEntry | None:
    lock_model = _coerce_lock_model(lock)
    if lock_model.bub is None:
        return None
    return lock_model.bub.to_entry()


def locked_contrib_entries(lock: dict[str, Any] | BubseekLock) -> list[LockedContribEntry]:
    """Read contrib entries from lock."""
    lock_model = _coerce_lock_model(lock)
    return [item.to_entry() for item in lock_model.contrib]


def locked_skill_entries(lock: dict[str, Any] | BubseekLock) -> list[LockedSkillEntry]:
    """Read skill entries from lock."""
    lock_model = _coerce_lock_model(lock)
    return [item.to_entry() for item in lock_model.skills]


def configured_contrib_packages(config: dict[str, Any] | BubseekConfig) -> list[str]:
    """Read configured contrib package names from config."""
    return [entry.name for entry in configured_contrib_entries(config) if entry.name is not None]


def configured_skill_paths(config: dict[str, Any] | BubseekConfig) -> list[str]:
    """Read configured local skill paths from config."""
    return [entry.path for entry in configured_skill_entries(config) if entry.kind == "local" and entry.path is not None]


def generate_config(
    *,
    config_path: str | Path | None = None,
    overwrite: bool = False,
    project_name: str = "bubseek",
    version: str = "0.1.0",
    contrib_packages: list[str] | None = None,
    contrib_repo_url: str = DEFAULT_CONTRIB_REPO,
    bub_path: str = DEFAULT_BUB_PATH,
) -> Path:
    """Generate `bubseek.toml` from current distribution layout."""
    path = Path(config_path).expanduser().resolve() if config_path is not None else distribution_root() / CONFIG_FILE_NAME
    if path.exists() and not overwrite:
        raise FileExistsError(f"config already exists: {path}")
    root = path.parent
    skill_paths = _discover_skill_paths(root)
    packages = contrib_packages if contrib_packages is not None else list(DEFAULT_CONTRIB_PACKAGES)
    content = _render_config(
        project_name=project_name,
        version=version,
        bub_path=bub_path,
        contrib_packages=packages,
        contrib_repo_url=contrib_repo_url,
        skill_paths=skill_paths,
    )
    path.write_text(content, encoding="utf-8")
    return path


def generate_lock(
    *,
    config_path: str | Path | None = None,
    lock_path: str | Path | None = None,
) -> Path:
    """Generate `bubseek.lock` from `bubseek.toml`."""
    resolved_config_path = resolve_config_path(config_path)
    config_model = load_config_model(resolved_config_path)
    resolved_lock_path = resolve_lock_path(lock_path, config_path=resolved_config_path)
    root = resolved_config_path.parent

    bub_entry = configured_bub_entry(config_model)
    contrib_entries = configured_contrib_entries(config_model)
    skill_entries = configured_skill_entries(config_model)
    if not skill_entries:
        skill_entries = [SourceEntry(name=Path(item).name, kind="local", path=item) for item in _discover_skill_paths(root)]

    lock_bub_entry = _lock_entry(entry=bub_entry, root=root, local_hasher=sha256_package_dir)
    lock_contrib_entries = [_lock_entry(entry=entry, root=root, local_hasher=sha256_package_dir) for entry in contrib_entries]
    lock_skill_entries = [_lock_entry(entry=entry, root=root, local_hasher=sha256_dir) for entry in skill_entries]

    content = _render_lock(
        config_file=resolved_config_path.name,
        config_sha256=sha256_file(resolved_config_path),
        bub_entry=lock_bub_entry,
        contrib_entries=lock_contrib_entries,
        skill_entries=lock_skill_entries,
    )
    resolved_lock_path.write_text(content, encoding="utf-8")
    return resolved_lock_path


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"invalid TOML payload: {path}")
    return data


def _coerce_config_model(config: dict[str, Any] | BubseekConfig) -> BubseekConfig:
    if isinstance(config, BubseekConfig):
        return config
    return BubseekConfig.model_validate(config)


def _coerce_lock_model(lock: dict[str, Any] | BubseekLock) -> BubseekLock:
    if isinstance(lock, BubseekLock):
        return lock
    return BubseekLock.model_validate(lock)


def _discover_skill_paths(root: Path) -> list[str]:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return []
    paths: list[str] = []
    for entry in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if not entry.is_dir():
            continue
        if not (entry / SKILL_FILE_NAME).is_file():
            continue
        paths.append(f"skills/{entry.name}")
    return paths


def _lock_entry(*, entry: SourceEntry, root: Path, local_hasher: Callable[[Path], str]) -> dict[str, str]:
    payload: dict[str, str] = {"kind": entry.kind}
    if entry.name is not None:
        payload["name"] = entry.name

    if entry.kind == "local":
        if entry.path is None:
            raise ValueError(f"local path missing: {entry.name or 'entry'}")
        rel_path = entry.path.replace("\\", "/")
        full_path = (root / rel_path).resolve()
        if not full_path.is_dir():
            raise FileNotFoundError(f"path not found: {rel_path}")
        payload["path"] = rel_path
        payload["sha256"] = local_hasher(full_path)
        return payload

    if entry.source is None:
        raise ValueError(f"remote source missing: {entry.name or 'entry'}")
    resolved_source = _resolve_lock_source(entry.source)
    payload["source"] = resolved_source.source
    payload["sha256"] = sha256_text(resolved_source.source)
    payload["resolved_commit"] = resolved_source.resolved_commit
    return payload


def _resolve_lock_source(source: str) -> ResolvedGitSource:
    repo, ref, subdirectory = _parse_git_source(source)
    resolved_ref = _resolve_git_ref(repo=repo, ref=ref)
    return ResolvedGitSource(
        source=_git_source(repo=repo, subdirectory=subdirectory, ref=resolved_ref),
        resolved_commit=resolved_ref,
    )


def _parse_git_source(source: str) -> tuple[str, str | None, str | None]:
    matched = GIT_SOURCE_RE.match(source)
    if matched is None:
        raise ValueError(f"unsupported git source: {source}")
    return matched.group("repo"), matched.group("ref"), matched.group("subdirectory")


def _validated_resolved_commit(*, source: str, resolved_commit: str | None) -> str:
    _, source_ref, _ = _parse_git_source(source)
    commit = resolved_commit or source_ref
    if commit is None or COMMIT_SHA_RE.fullmatch(commit) is None:
        raise ValueError(f"resolved commit missing or invalid for source: {source}")
    if source_ref != commit:
        raise ValueError(f"source ref does not match resolved_commit: {source}")
    return commit


def _infer_locked_kind(*, path: str | None, source: str | None) -> Literal["local", "remote"]:
    if source is not None:
        return "remote"
    if path is not None:
        return "local"
    raise ValueError("locked kind could not be inferred")


def _resolve_git_ref(*, repo: str, ref: str | None) -> str:
    if ref is not None and COMMIT_SHA_RE.fullmatch(ref):
        return ref

    patterns = ["HEAD"] if ref is None else [f"refs/heads/{ref}", f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}", ref]
    executable = shutil.which("git")
    if executable is None:
        raise FileNotFoundError("command not found: git")
    completed = subprocess.run(
        [executable, "ls-remote", repo, *patterns],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in completed.stdout.splitlines():
        commit, _, _name = line.partition("\t")
        if COMMIT_SHA_RE.fullmatch(commit):
            return commit
    target = ref or "HEAD"
    raise ValueError(f"unable to resolve git ref '{target}' for {repo}")


def _git_source(*, repo: str, subdirectory: str | None, ref: str | None) -> str:
    normalized_repo = repo.rstrip("/")
    if not normalized_repo.endswith(".git"):
        normalized_repo = f"{normalized_repo}.git"
    suffix = f"#subdirectory={subdirectory}" if subdirectory else ""
    if ref:
        return f"git+{normalized_repo}@{ref}{suffix}"
    return f"git+{normalized_repo}{suffix}"


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_dir(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        relative_path = file_path.relative_to(path).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def sha256_package_dir(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in _package_hash_files(path):
        relative_path = file_path.relative_to(path).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def verify_local_package_dir(*, path: Path, expected_sha256: str, error_message: str) -> None:
    actual_sha256 = sha256_package_dir(path)
    if actual_sha256 != expected_sha256:
        raise ValueError(error_message)


def _package_hash_files(root: Path) -> list[Path]:
    package_files = _declared_package_files(root)
    if package_files is not None:
        return package_files
    return [
        file_path
        for file_path in sorted(item for item in root.rglob("*") if item.is_file())
        if not any(part in IGNORED_TREE_NAMES for part in file_path.relative_to(root).parts)
    ]


def _declared_package_files(root: Path) -> list[Path] | None:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return None
    try:
        pyproject_data = _load_toml(pyproject_path)
    except Exception:
        return None

    files: set[Path] = {pyproject_path}
    _maybe_add_readme(files=files, root=root, pyproject_data=pyproject_data)
    for include in _declared_build_includes(pyproject_data):
        _add_included_path(files=files, root=root, include=include)

    return sorted(files)


def _maybe_add_readme(*, files: set[Path], root: Path, pyproject_data: dict[str, Any]) -> None:
    project = pyproject_data.get("project")
    if not isinstance(project, dict):
        return
    readme = project.get("readme")
    if not isinstance(readme, str):
        return
    readme_path = (root / readme).resolve()
    if readme_path.is_file() and readme_path.is_relative_to(root):
        files.add(readme_path)


def _declared_build_includes(pyproject_data: dict[str, Any]) -> list[str]:
    tool = pyproject_data.get("tool")
    if not isinstance(tool, dict):
        return []
    pdm = tool.get("pdm")
    if not isinstance(pdm, dict):
        return []
    build = pdm.get("build")
    if not isinstance(build, dict):
        return []
    includes = build.get("includes")
    if not isinstance(includes, list):
        return []
    return [item for item in includes if isinstance(item, str) and item.strip()]


def _add_included_path(*, files: set[Path], root: Path, include: str) -> None:
    include_path = (root / include).resolve()
    if not include_path.exists() or not include_path.is_relative_to(root):
        return
    if include_path.is_file():
        files.add(include_path)
        return
    for file_path in include_path.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in IGNORED_TREE_NAMES for part in file_path.relative_to(root).parts):
            continue
        files.add(file_path.resolve())


def _render_config(
    *,
    project_name: str,
    version: str,
    bub_path: str,
    contrib_packages: list[str],
    contrib_repo_url: str,
    skill_paths: list[str],
) -> str:
    lines = [
        "[project]",
        f'name = "{project_name}"',
        f'version = "{version}"',
        "",
        "[bub]",
        f'path = "{bub_path}"',
        "",
    ]
    for package in contrib_packages:
        lines.extend(
            [
                "[[contrib]]",
                f'name = "{package}"',
                f'repo = "{contrib_repo_url}"',
                f'path = "packages/{package}"',
                'ref = "main"',
                "",
            ]
        )
    for skill_path in skill_paths:
        lines.extend(
            [
                "[[skills]]",
                f'name = "{Path(skill_path).name}"',
                f'path = "{skill_path}"',
                "",
            ]
        )
    return "\n".join(lines)


def _render_lock(
    *,
    config_file: str,
    config_sha256: str,
    bub_entry: dict[str, str] | None,
    contrib_entries: list[dict[str, str]],
    skill_entries: list[dict[str, str]],
) -> str:
    lines = [
        "[meta]",
        "lock_version = 1",
        f'config_file = "{config_file}"',
        f'config_sha256 = "{config_sha256}"',
        "",
    ]
    if bub_entry is not None:
        lines.extend(_render_locked_section(header="[bub]", entry=bub_entry))
    for entry in contrib_entries:
        lines.extend(_render_locked_section(header="[[contrib]]", entry=entry))
    for entry in skill_entries:
        lines.extend(_render_locked_section(header="[[skills]]", entry=entry))
    return "\n".join(lines)


def _render_locked_section(*, header: str, entry: dict[str, str]) -> list[str]:
    lines = [header]
    if "name" in entry:
        lines.append(f'name = "{entry["name"]}"')
    lines.append(f'kind = "{entry["kind"]}"')
    lines.append(f'sha256 = "{entry["sha256"]}"')
    if entry["kind"] == "local":
        lines.append(f'path = "{entry["path"]}"')
    else:
        lines.append(f'source = "{entry["source"]}"')
        lines.append(f'resolved_commit = "{entry["resolved_commit"]}"')
    lines.append("")
    return lines
