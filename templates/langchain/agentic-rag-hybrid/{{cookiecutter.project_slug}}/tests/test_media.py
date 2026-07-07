from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from {{ cookiecutter.project_slug }}.media import extract_archive_safely, scan_images


def test_scan_images_returns_supported_files_in_stable_order(tmp_path: Path) -> None:
    (tmp_path / "b.png").write_bytes(b"fake")
    (tmp_path / "a.jpg").write_bytes(b"fake")
    (tmp_path / ".hidden.jpg").write_bytes(b"fake")
    (tmp_path / "notes.txt").write_text("not image")

    assert [path.name for path in scan_images(tmp_path)] == ["a.jpg", "b.png"]


def test_scan_images_does_not_follow_symlinks(tmp_path: Path) -> None:
    real = tmp_path / "real.png"
    real.write_bytes(b"fake")
    (tmp_path / "linked.png").symlink_to(real)

    assert [path.name for path in scan_images(tmp_path)] == ["real.png"]


def test_extract_archive_safely_rejects_zip_slip(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.jpg", "bad")

    with pytest.raises(ValueError, match="Unsafe archive member"):
        extract_archive_safely(archive, tmp_path / "out")


def test_extract_archive_safely_rejects_tar_links(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w") as tf:
        member = tarfile.TarInfo("linked.png")
        member.type = tarfile.SYMTYPE
        member.linkname = "/etc/passwd"
        tf.addfile(member)

    with pytest.raises(ValueError, match="Unsupported archive member"):
        extract_archive_safely(archive, tmp_path / "out")


def test_extract_archive_safely_rejects_total_expanded_size(tmp_path: Path) -> None:
    archive = tmp_path / "large.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("one.png", b"123456")
        zf.writestr("two.png", b"123456")

    with pytest.raises(ValueError, match="Archive expands beyond allowed size"):
        extract_archive_safely(
            archive,
            tmp_path / "out",
            max_member_bytes=10,
            max_total_bytes=10,
        )


def test_extract_archive_safely_rejects_too_many_members(tmp_path: Path) -> None:
    archive = tmp_path / "many.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("one.png", b"1")
        zf.writestr("two.png", b"2")

    with pytest.raises(ValueError, match="Too many archive members"):
        extract_archive_safely(archive, tmp_path / "out", max_members=1)
