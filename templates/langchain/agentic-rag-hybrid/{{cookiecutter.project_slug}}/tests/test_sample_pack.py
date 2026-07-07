from __future__ import annotations

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
        assert (image_dir / item["file_name"]).is_file()
        assert item["caption"]
        assert item["tags"]
    assert sample_pack_path().is_file()


def test_sample_pack_cases_cover_all_hybrid_modes() -> None:
    modes = {case["recommended_mode"] for case in sample_pack_cases()}
    assert modes == {"semantic", "keyword", "exact", "balanced"}
