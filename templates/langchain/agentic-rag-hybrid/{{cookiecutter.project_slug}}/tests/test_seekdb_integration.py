from __future__ import annotations

import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from {{ cookiecutter.project_slug }}.settings import Settings
from {{ cookiecutter.project_slug }}.store import HybridImageStore


pytest.importorskip("pylibseekdb", reason="embedded seekdb bindings are unavailable on this platform")


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class DeterministicEmbeddingEngine:
    """Small local vectors that keep the seekdb integration proof network-free."""

    def embed_image(self, image_path: Path) -> list[float]:
        if image_path.name.startswith("sunset-lake"):
            return [1.0, 0.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0, 0.0]

    def embed_text(self, text: str) -> list[float]:
        if text == "quiet water at dusk":
            return [1.0, 0.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0, 0.0]


def _run_real_seekdb_integration(root: Path, seekdb_path: Path) -> None:
    fixture_dir = root / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "sunset-lake.png").write_bytes(PNG_1X1)
    (fixture_dir / "city-train.png").write_bytes(PNG_1X1)
    (fixture_dir / "manifest.yml").write_text(
        """images:
  - id: sunset-lake
    file_name: sunset-lake.png
    caption: Crimson sunset above a mountain lake.
    tags: [landscape, evening]
  - id: city-train
    file_name: city-train.png
    caption: Silver train waiting at an urban platform.
    tags: [transit, daytime]
""",
        encoding="utf-8",
    )
    settings = Settings(
        seekdb_path=seekdb_path,
        seekdb_db_name="test",
        image_table_name="image_records",
        embedding_type="deterministic",
        embedding_api_key="",
        embedding_base_url="",
        embedding_model="deterministic-test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="",
        vlm_model="unused",
        hybrid_default_mode="semantic",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=root / "managed-media",
        media_max_upload_bytes=1024,
    )

    store = HybridImageStore(
        settings=settings,
        embedding_engine=DeterministicEmbeddingEngine(),
    )

    vector_store_type = type(store.vector_store)
    assert vector_store_type.__name__ == "OceanbaseVectorStore"
    assert vector_store_type.__module__.startswith("langchain_oceanbase.")

    records = store.ingest_directory(fixture_dir)

    assert {record.caption for record in records} == {
        "Crimson sunset above a mountain lake.",
        "Silver train waiting at an urban platform.",
    }
    assert len(records) == 2
    for record in records:
        assert record.file_path.parent == settings.media_data_dir / "images"
        assert record.file_path.is_file()
        assert record.file_path.read_bytes() == PNG_1X1

    trace = store.search_text("quiet water at dusk", mode="semantic", top_k=1)

    assert trace.hits
    assert trace.hits[0].file_name == "sunset-lake.png"
    assert trace.hits[0].caption == "Crimson sunset above a mountain lake."


def test_real_seekdb_persists_images_and_serves_semantic_text_search(tmp_path: Path) -> None:
    # A child process gives the native engine a definitive shutdown boundary.
    # Keep its database path short enough for macOS local sockets.
    seekdb_path = Path(tempfile.mkdtemp(prefix="agentseek-seekdb-", dir="/tmp"))
    try:
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(Path(__file__).resolve()), str(tmp_path), str(seekdb_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        shutil.rmtree(seekdb_path, ignore_errors=True)


if __name__ == "__main__":
    _run_real_seekdb_integration(Path(sys.argv[1]), Path(sys.argv[2]))
