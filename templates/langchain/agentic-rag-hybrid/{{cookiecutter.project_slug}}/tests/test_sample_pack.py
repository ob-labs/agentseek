from __future__ import annotations

import zipfile

from {{ cookiecutter.project_slug }}.sample_pack import (
    sample_pack_cases,
    sample_pack_dir,
    sample_pack_manifest,
    sample_pack_path,
)


def test_sample_pack_manifest_matches_image_files() -> None:
    manifest = sample_pack_manifest()
    image_dir = sample_pack_dir() / "images"
    for item in manifest["images"]:
        image_path = image_dir / item["file_name"]
        assert image_path.is_file()
        assert image_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert item["caption"]
        assert item["tags"]
    assert sample_pack_path().is_file()
    with zipfile.ZipFile(sample_pack_path()) as archive:
        names = set(archive.namelist())
        zipped_images = {
            name.removeprefix("images/"): archive.read(name)
            for name in names
            if name.startswith("images/")
        }
    assert "manifest.yml" in names
    for item in manifest["images"]:
        assert f"images/{item['file_name']}" in names
        assert zipped_images[item["file_name"]] == (image_dir / item["file_name"]).read_bytes()


def test_sample_pack_cases_cover_all_hybrid_modes() -> None:
    modes = {case["recommended_mode"] for case in sample_pack_cases()}
    assert modes == {"semantic", "keyword", "exact", "balanced"}


def test_sample_pack_cases_have_mode_specific_expected_winners() -> None:
    image_ids = {item["id"] for item in sample_pack_manifest()["images"]}
    modes = {"semantic", "keyword", "exact", "balanced"}
    for case in sample_pack_cases():
        winners = case["expected_top_by_mode"]
        assert set(winners) == modes
        assert set(winners.values()).issubset(image_ids)
        assert len(set(winners.values())) >= 2
