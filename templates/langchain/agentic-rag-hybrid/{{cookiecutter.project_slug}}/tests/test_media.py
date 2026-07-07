from __future__ import annotations

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


def test_extract_archive_safely_rejects_zip_slip(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.jpg", "bad")

    with pytest.raises(ValueError, match="Unsafe archive member"):
        extract_archive_safely(archive, tmp_path / "out")
