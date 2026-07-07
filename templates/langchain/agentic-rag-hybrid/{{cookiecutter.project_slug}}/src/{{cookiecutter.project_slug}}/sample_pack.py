from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def examples_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples"


def sample_pack_dir() -> Path:
    return examples_dir() / "sample_pack"


def sample_pack_path() -> Path:
    return sample_pack_dir() / "sample_pack.zip"


def sample_pack_manifest() -> dict[str, Any]:
    manifest_path = sample_pack_dir() / "manifest.yml"
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def sample_pack_cases() -> list[dict[str, Any]]:
    cases_path = examples_dir() / "hybrid_cases.yml"
    data = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    return list(data["cases"])
