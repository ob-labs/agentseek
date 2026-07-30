"""Verify that checked-in and built AgentSeek release versions agree."""

from __future__ import annotations

import argparse
import email.parser
import json
import shutil
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

_SOURCE_CATALOG_LOCK = Path("src/agentseek/data/catalog-lock.json")
_WHEEL_CATALOG_LOCK = "agentseek/data/catalog-lock.json"
_SOURCE_RELEASE_FILES = (
    Path("README.md"),
    Path("README.zh.md"),
    Path("diagram/agentseek-readme/agentseek-adlc-en.svg"),
    Path("diagram/agentseek-readme/agentseek-adlc-en@2x.png"),
    Path("diagram/agentseek-readme/agentseek-adlc-zh.svg"),
    Path("diagram/agentseek-readme/agentseek-adlc-zh@2x.png"),
    Path("diagram/agentseek-readme/agentseek-architecture-en.svg"),
    Path("diagram/agentseek-readme/agentseek-architecture-en@2x.png"),
    Path("diagram/agentseek-readme/agentseek-architecture-zh.svg"),
    Path("diagram/agentseek-readme/agentseek-architecture-zh@2x.png"),
)
_BUILD_SKILL_NAMES = ("friendly-python", "piglet")
_BUILD_SKILL_SOURCE = {
    "git": "https://github.com/PsiACE/skills.git",
    "ref": "4f09937234d128656fdc8c8658c840ebbf7e28d1",
    "subpath": "skills",
    "include": list(_BUILD_SKILL_NAMES),
}


class ReleaseVersionError(ValueError):
    """Release metadata is missing or inconsistent."""


def project_version(root: Path) -> str:
    """Return the AgentSeek version declared by ``pyproject.toml``."""
    with (root / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def source_pyproject(root: Path) -> bytes:
    """Return the exact project metadata committed for the release."""
    try:
        return (root / "pyproject.toml").read_bytes()
    except OSError as exc:
        message = "source pyproject.toml is unavailable"
        raise ReleaseVersionError(message) from exc


def verify_build_skill_source(raw: bytes, *, surface: str) -> None:
    """Require build-vendored skills to use the reviewed immutable source."""
    try:
        skills = tomllib.loads(raw.decode("utf-8"))["tool"]["pdm"]["build"]["skills"]
    except (KeyError, TypeError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        message = f"{surface} has no valid build skill source"
        raise ReleaseVersionError(message) from exc
    if skills != [_BUILD_SKILL_SOURCE]:
        message = f"{surface} build skill source is not pinned to the reviewed commit"
        raise ReleaseVersionError(message)


def lock_version(root: Path) -> str:
    """Return the root AgentSeek package version recorded by ``uv.lock``."""
    with (root / "uv.lock").open("rb") as stream:
        packages = tomllib.load(stream)["package"]
    matches = [str(package["version"]) for package in packages if package.get("name") == "agentseek"]
    if len(matches) != 1:
        message = "uv.lock must contain exactly one agentseek package"
        raise ReleaseVersionError(message)
    return matches[0]


def _wheel_metadata(wheel: Path) -> bytes:
    """Return the single core METADATA payload from *wheel*."""
    with zipfile.ZipFile(wheel) as archive:
        candidates = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(candidates) != 1:
            message = "wheel must contain exactly one METADATA file"
            raise ReleaseVersionError(message)
        return archive.read(candidates[0])


def wheel_version(wheel: Path) -> str:
    """Return the AgentSeek version from a built wheel's core metadata."""
    metadata = email.parser.BytesParser().parsebytes(_wheel_metadata(wheel))
    if metadata.get("Name", "").casefold() != "agentseek":
        message = "wheel metadata does not describe agentseek"
        raise ReleaseVersionError(message)
    version = metadata.get("Version")
    if version is None:
        message = "wheel metadata has no Version field"
        raise ReleaseVersionError(message)
    return version


def wheel_readme(wheel: Path) -> bytes:
    """Return the exact long-description body carried by wheel METADATA."""
    metadata = _wheel_metadata(wheel)
    for separator in (b"\r\n\r\n", b"\n\n"):
        if separator in metadata:
            body = metadata.partition(separator)[2]
            if body:
                return body
            break
    message = "wheel METADATA has no README.md long description"
    raise ReleaseVersionError(message)


def source_catalog_lock(root: Path) -> bytes:
    """Return the exact catalog lock bytes committed for the release."""
    try:
        return (root / _SOURCE_CATALOG_LOCK).read_bytes()
    except OSError as exc:
        message = "source catalog lock is unavailable"
        raise ReleaseVersionError(message) from exc


def source_release_files(root: Path) -> dict[str, bytes]:
    """Return the exact README and diagram bytes committed for the release."""
    payload: dict[str, bytes] = {}
    for relative in _SOURCE_RELEASE_FILES:
        try:
            payload[relative.as_posix()] = (root / relative).read_bytes()
        except OSError as exc:
            message = f"source release asset {relative.as_posix()} is unavailable"
            raise ReleaseVersionError(message) from exc
    return payload


def _required_catalog_string(lock: dict[str, object], field: str) -> str:
    value = lock.get(field)
    if not isinstance(value, str) or not value:
        message = f"catalog-lock.json {field} must be a non-empty string"
        raise ReleaseVersionError(message)
    return value


def _remote_tag_commit(repository: str, release: str) -> str:
    reference = f"refs/tags/{release}"
    peeled = f"{reference}^{{}}"
    git = shutil.which("git")
    if git is None:
        message = "git is required to verify protected release tags"
        raise ReleaseVersionError(message)
    try:
        output = subprocess.check_output(  # noqa: S603 - no shell; lock fields are passed as inert arguments.
            [git, "ls-remote", "--tags", "--", repository, reference, peeled],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        message = f"could not resolve protected release tag {release!r} from {repository}"
        raise ReleaseVersionError(message) from exc
    references: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            references[parts[1]] = parts[0]
    commit = references.get(peeled) or references.get(reference)
    if commit is None:
        message = f"protected release tag {release!r} is missing from {repository}"
        raise ReleaseVersionError(message)
    return commit


def verify_remote_release_tags(raw: bytes) -> None:
    """Require both human-readable lock tags to retain their exact commits."""
    try:
        lock = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = "source catalog lock is not valid UTF-8 JSON"
        raise ReleaseVersionError(message) from exc
    if not isinstance(lock, dict):
        message = "source catalog lock must be a JSON object"
        raise ReleaseVersionError(message)

    for prefix in ("catalog", "core"):
        repository = _required_catalog_string(lock, f"{prefix}_repository")
        release = _required_catalog_string(lock, f"{prefix}_release")
        expected_commit = _required_catalog_string(lock, f"{prefix}_commit")
        actual_commit = _remote_tag_commit(repository, release)
        if actual_commit != expected_commit:
            message = (
                f"{prefix}_release {release!r} resolves to {actual_commit}, not the locked commit {expected_commit}"
            )
            raise ReleaseVersionError(message)


def wheel_catalog_lock(wheel: Path) -> bytes:
    """Return the exact catalog lock bytes packaged in *wheel*."""
    with zipfile.ZipFile(wheel) as archive:
        candidates = [name for name in archive.namelist() if name == _WHEEL_CATALOG_LOCK]
        if not candidates:
            message = "wheel has no catalog lock"
            raise ReleaseVersionError(message)
        if len(candidates) != 1:
            message = "wheel must contain exactly one catalog lock"
            raise ReleaseVersionError(message)
        return archive.read(candidates[0])


def _sdist_member(sdist: Path, relative: str) -> bytes:
    try:
        with tarfile.open(sdist, mode="r:gz") as archive:
            candidates = [
                member
                for member in archive.getmembers()
                if member.isfile() and member.name.partition("/")[2] == relative
            ]
            if len(candidates) != 1:
                message = f"sdist must contain exactly one {relative}"
                raise ReleaseVersionError(message)
            stream = archive.extractfile(candidates[0])
            if stream is None:
                message = f"sdist {relative} is unreadable"
                raise ReleaseVersionError(message)
            return stream.read()
    except (OSError, tarfile.TarError) as exc:
        message = "sdist is not a readable gzip tar archive"
        raise ReleaseVersionError(message) from exc


def sdist_version(sdist: Path) -> str:
    """Return the AgentSeek version from an sdist's package metadata."""
    metadata = email.parser.BytesParser().parsebytes(_sdist_member(sdist, "PKG-INFO"))
    if metadata.get("Name", "").casefold() != "agentseek":
        message = "sdist metadata does not describe agentseek"
        raise ReleaseVersionError(message)
    version = metadata.get("Version")
    if version is None:
        message = "sdist metadata has no Version field"
        raise ReleaseVersionError(message)
    return version


def sdist_catalog_lock(sdist: Path) -> bytes:
    """Return the catalog lock packaged in *sdist*."""
    return _sdist_member(sdist, "src/agentseek/data/catalog-lock.json")


def verify_wheel_skill_payload(wheel: Path, skills_root: Path) -> None:
    """Compare vendored wheel skills byte-for-byte with the pinned checkout."""
    expected: dict[str, bytes] = {}
    for skill in _BUILD_SKILL_NAMES:
        source = skills_root / skill
        if not source.is_dir():
            message = f"pinned skill source is missing {skill}"
            raise ReleaseVersionError(message)
        files = [path for path in sorted(source.rglob("*")) if path.is_file()]
        if not files:
            message = f"pinned skill source {skill} is empty"
            raise ReleaseVersionError(message)
        try:
            for path in files:
                relative = path.relative_to(source).as_posix()
                expected[f"skills/{skill}/{relative}"] = path.read_bytes()
        except OSError as exc:
            message = f"pinned skill source {skill} is unreadable"
            raise ReleaseVersionError(message) from exc
    try:
        with zipfile.ZipFile(wheel) as archive:
            prefixes = tuple(f"skills/{skill}/" for skill in _BUILD_SKILL_NAMES)
            members = [info for info in archive.infolist() if not info.is_dir() and info.filename.startswith(prefixes)]
            if len({info.filename for info in members}) != len(members):
                message = "wheel contains duplicate vendored skill paths"
                raise ReleaseVersionError(message)
            actual = {info.filename: archive.read(info) for info in members}
    except (OSError, zipfile.BadZipFile) as exc:
        message = "wheel is not a readable ZIP archive"
        raise ReleaseVersionError(message) from exc
    if actual != expected:
        message = "wheel vendored skill payload does not match the pinned checkout"
        raise ReleaseVersionError(message)


def _verify_wheel_release_files(wheel: Path, catalog_lock: bytes, release_files: dict[str, bytes]) -> None:
    if wheel_catalog_lock(wheel) != catalog_lock:
        message = "wheel catalog lock does not match the committed catalog lock"
        raise ReleaseVersionError(message)
    if wheel_readme(wheel) != release_files["README.md"]:
        message = "wheel METADATA long description does not match committed README.md"
        raise ReleaseVersionError(message)


def _verify_sdist_release_files(sdist: Path, catalog_lock: bytes, release_files: dict[str, bytes]) -> None:
    if sdist_catalog_lock(sdist) != catalog_lock:
        message = "sdist catalog lock does not match the committed catalog lock"
        raise ReleaseVersionError(message)
    verify_build_skill_source(
        _sdist_member(sdist, "pyproject.toml"),
        surface="sdist pyproject.toml",
    )
    for relative, expected_bytes in release_files.items():
        if _sdist_member(sdist, relative) != expected_bytes:
            message = f"sdist {relative} does not match committed source"
            raise ReleaseVersionError(message)


def verify_release_version(
    expected: str,
    *,
    root: Path,
    wheel: Path | None = None,
    sdist: Path | None = None,
    skills_root: Path | None = None,
    verify_remote_tags: bool = False,
) -> None:
    """Raise when any release surface differs from *expected*."""
    pyproject = source_pyproject(root)
    verify_build_skill_source(pyproject, surface="source pyproject.toml")
    catalog_lock = source_catalog_lock(root)
    versions = {
        "pyproject.toml": project_version(root),
        "uv.lock": lock_version(root),
    }
    if wheel is not None:
        versions[str(wheel)] = wheel_version(wheel)
    if sdist is not None:
        versions[str(sdist)] = sdist_version(sdist)
    mismatches = {surface: version for surface, version in versions.items() if version != expected}
    if mismatches:
        rendered = ", ".join(f"{surface}={version}" for surface, version in mismatches.items())
        message = f"expected release version {expected}; found {rendered}"
        raise ReleaseVersionError(message)
    release_files = source_release_files(root) if wheel is not None or sdist is not None else {}
    if wheel is not None:
        _verify_wheel_release_files(wheel, catalog_lock, release_files)
    if sdist is not None:
        _verify_sdist_release_files(sdist, catalog_lock, release_files)
    if skills_root is not None:
        if wheel is None:
            message = "--skills-root requires --wheel"
            raise ReleaseVersionError(message)
        verify_wheel_skill_payload(wheel, skills_root)
    if verify_remote_tags:
        verify_remote_release_tags(catalog_lock)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", help="Expected version without a leading v")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--sdist", type=Path)
    parser.add_argument("--skills-root", type=Path)
    parser.add_argument("--verify-remote-tags", action="store_true")
    args = parser.parse_args()
    verify_release_version(
        args.expected,
        root=args.root,
        wheel=args.wheel,
        sdist=args.sdist,
        skills_root=args.skills_root,
        verify_remote_tags=args.verify_remote_tags,
    )


if __name__ == "__main__":
    main()
