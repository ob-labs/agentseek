from __future__ import annotations

import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from agentseek.release import verify_release_version, verify_remote_release_tags

_PINNED_SKILLS_REF = "4f09937234d128656fdc8c8658c840ebbf7e28d1"


def _pyproject_bytes(version: str, *, skills_ref: str = _PINNED_SKILLS_REF) -> bytes:
    return (
        f'[project]\nname = "agentseek"\nversion = "{version}"\n\n'
        "[tool.pdm.build]\n"
        "skills = [\n"
        '  { git = "https://github.com/PsiACE/skills.git", '
        f'ref = "{skills_ref}", subpath = "skills", '
        'include = ["friendly-python", "piglet"] },\n'
        "]\n"
    ).encode()


def _catalog_lock_bytes(
    version: str,
    *,
    catalog_release: str | None = None,
    core_release: str | None = None,
) -> bytes:
    return json.dumps(
        {
            "catalog_repository": "https://github.com/agentseek-ai/agentseek-templates.git",
            "catalog_commit": "1" * 40,
            "catalog_release": catalog_release or f"v{version}",
            "core_repository": "https://github.com/ob-labs/agentseek.git",
            "core_commit": "2" * 40,
            "core_release": core_release or f"core-snapshot-v{version}",
        },
        separators=(",", ":"),
    ).encode()


def _write_release_surfaces(
    root: Path,
    version: str,
    *,
    catalog_release: str | None = None,
    core_release: str | None = None,
) -> bytes:
    (root / "pyproject.toml").write_bytes(_pyproject_bytes(version))
    (root / "uv.lock").write_text(
        f'[[package]]\nname = "agentseek"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    lock_bytes = _catalog_lock_bytes(
        version,
        catalog_release=catalog_release,
        core_release=core_release,
    )
    lock_path = root / "src" / "agentseek" / "data" / "catalog-lock.json"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_bytes(lock_bytes)
    return lock_bytes


def _write_wheel(
    root: Path,
    version: str,
    *,
    catalog_lock: bytes | None = None,
    include_catalog_lock: bool = True,
    skill_payload: dict[str, bytes] | None = None,
) -> Path:
    wheel = root / f"agentseek-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"agentseek-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: agentseek\nVersion: {version}\n",
        )
        if include_catalog_lock:
            archive.writestr(
                "agentseek/data/catalog-lock.json",
                catalog_lock
                if catalog_lock is not None
                else (root / "src" / "agentseek" / "data" / "catalog-lock.json").read_bytes(),
            )
        for relative, content in (skill_payload or {}).items():
            archive.writestr(f"skills/{relative}", content)
    return wheel


def _write_sdist(
    root: Path,
    version: str,
    *,
    catalog_lock: bytes | None = None,
    pyproject: bytes | None = None,
) -> Path:
    sdist = root / f"agentseek-{version}.tar.gz"
    prefix = f"agentseek-{version}"

    def add(archive: tarfile.TarFile, relative: str, content: bytes) -> None:
        member = tarfile.TarInfo(f"{prefix}/{relative}")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))

    with tarfile.open(sdist, "w:gz") as archive:
        add(
            archive,
            "PKG-INFO",
            f"Metadata-Version: 2.4\nName: agentseek\nVersion: {version}\n".encode(),
        )
        add(archive, "pyproject.toml", pyproject or _pyproject_bytes(version))
        add(
            archive,
            "src/agentseek/data/catalog-lock.json",
            catalog_lock
            if catalog_lock is not None
            else (root / "src" / "agentseek" / "data" / "catalog-lock.json").read_bytes(),
        )
    return sdist


def test_release_versions_match_across_all_distribution_surfaces(tmp_path: Path) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")

    verify_release_version(
        "0.1.0",
        root=tmp_path,
        wheel=_write_wheel(tmp_path, "0.1.0"),
        sdist=_write_sdist(tmp_path, "0.1.0"),
    )


@pytest.mark.parametrize("surface", ["project", "lock", "wheel", "sdist"])
def test_release_version_mismatch_is_rejected(tmp_path: Path, surface: str) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")
    wheel = _write_wheel(tmp_path, "0.1.0")
    sdist = _write_sdist(tmp_path, "0.1.0")
    if surface == "project":
        (tmp_path / "pyproject.toml").write_bytes(_pyproject_bytes("0.0.5"))
    elif surface == "lock":
        (tmp_path / "uv.lock").write_text(
            '[[package]]\nname = "agentseek"\nversion = "0.0.5"\n',
            encoding="utf-8",
        )
    elif surface == "wheel":
        wheel = _write_wheel(tmp_path, "0.0.5")
    else:
        sdist = _write_sdist(tmp_path, "0.0.5")

    with pytest.raises(ValueError, match=r"expected release version 0\.1\.0"):
        verify_release_version("0.1.0", root=tmp_path, wheel=wheel, sdist=sdist)


def test_dependency_release_names_are_independent_of_core_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_release_surfaces(
        tmp_path,
        "0.1.1",
        catalog_release="v0.1.0",
        core_release="core-snapshot-v0.1.0",
    )
    monkeypatch.setattr(
        "agentseek.release.subprocess.check_output",
        lambda command, **_kwargs: f"{'1' * 40 if 'agentseek-templates' in command[4] else '2' * 40}\t{command[-1]}\n",
    )

    verify_release_version("0.1.1", root=tmp_path, verify_remote_tags=True)


def test_wheel_catalog_lock_must_equal_the_committed_bytes(tmp_path: Path) -> None:
    source_lock = _write_release_surfaces(tmp_path, "0.1.0")
    wheel = _write_wheel(tmp_path, "0.1.0", catalog_lock=source_lock + b"\n")

    with pytest.raises(ValueError, match="catalog lock does not match"):
        verify_release_version("0.1.0", root=tmp_path, wheel=wheel)


def test_wheel_must_contain_the_catalog_lock(tmp_path: Path) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")
    wheel = _write_wheel(tmp_path, "0.1.0", include_catalog_lock=False)

    with pytest.raises(ValueError, match="wheel has no catalog lock"):
        verify_release_version("0.1.0", root=tmp_path, wheel=wheel)


def test_build_skill_source_must_be_pinned_to_the_reviewed_commit(tmp_path: Path) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")
    (tmp_path / "pyproject.toml").write_bytes(_pyproject_bytes("0.1.0", skills_ref="main"))

    with pytest.raises(ValueError, match="build skill source is not pinned"):
        verify_release_version("0.1.0", root=tmp_path)


def test_sdist_must_contain_the_committed_catalog_and_pinned_skill_source(tmp_path: Path) -> None:
    source_lock = _write_release_surfaces(tmp_path, "0.1.0")
    wrong_lock = _write_sdist(tmp_path, "0.1.0", catalog_lock=source_lock + b"\n")

    with pytest.raises(ValueError, match="sdist catalog lock does not match"):
        verify_release_version("0.1.0", root=tmp_path, sdist=wrong_lock)

    mutable_source = _write_sdist(
        tmp_path,
        "0.1.0",
        pyproject=_pyproject_bytes("0.1.0", skills_ref="main"),
    )
    with pytest.raises(ValueError, match=r"sdist pyproject\.toml build skill source is not pinned"):
        verify_release_version("0.1.0", root=tmp_path, sdist=mutable_source)


def test_wheel_vendored_skills_must_match_the_pinned_checkout(tmp_path: Path) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")
    skills_root = tmp_path / "pinned-skills"
    payload = {
        "friendly-python/SKILL.md": b"friendly\n",
        "piglet/SKILL.md": b"piglet\n",
    }
    for relative, content in payload.items():
        path = skills_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    wheel = _write_wheel(tmp_path, "0.1.0", skill_payload=payload)
    verify_release_version("0.1.0", root=tmp_path, wheel=wheel, skills_root=skills_root)

    wheel = _write_wheel(
        tmp_path,
        "0.1.0",
        skill_payload={**payload, "piglet/SKILL.md": b"drifted\n"},
    )
    with pytest.raises(ValueError, match="vendored skill payload does not match"):
        verify_release_version("0.1.0", root=tmp_path, wheel=wheel, skills_root=skills_root)


def test_skill_payload_verification_requires_a_wheel(tmp_path: Path) -> None:
    _write_release_surfaces(tmp_path, "0.1.0")

    with pytest.raises(ValueError, match="--skills-root requires --wheel"):
        verify_release_version("0.1.0", root=tmp_path, skills_root=tmp_path)


def test_remote_release_tags_must_resolve_to_the_locked_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _catalog_lock_bytes("0.1.0")
    calls: list[list[str]] = []

    def check_output(command: list[str], **_kwargs: object) -> str:
        calls.append(command)
        commit = "1" * 40 if "agentseek-templates" in command[4] else "2" * 40
        return f"{'0' * 40}\t{command[-2]}\n{commit}\t{command[-1]}\n"

    monkeypatch.setattr("agentseek.release.subprocess.check_output", check_output)

    verify_remote_release_tags(raw)

    assert [command[4] for command in calls] == [
        "https://github.com/agentseek-ai/agentseek-templates.git",
        "https://github.com/ob-labs/agentseek.git",
    ]


def test_remote_release_tag_mismatch_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agentseek.release.subprocess.check_output",
        lambda command, **_kwargs: f"{'0' * 40}\t{command[-1]}\n",
    )

    with pytest.raises(ValueError, match="not the locked commit"):
        verify_remote_release_tags(_catalog_lock_bytes("0.1.0"))
