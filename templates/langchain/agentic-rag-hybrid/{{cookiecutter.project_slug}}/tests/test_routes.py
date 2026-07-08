from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from {{ cookiecutter.project_slug }} import routes
from {{ cookiecutter.project_slug }}.routes import app
from {{ cookiecutter.project_slug }}.settings import Settings


def settings_for(tmp_path: Path, *, max_top_k: int = 3) -> Settings:
    return Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=max_top_k,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )


def test_custom_route_paths_are_mounted_under_custom_prefix() -> None:
    paths = {route.path for route in app.routes}
    assert "/custom/health" in paths
    assert "/custom/observability" in paths
    assert "/custom/sample-pack" in paths
    assert "/custom/sample-pack/ingest" in paths
    assert "/custom/sample-pack/download" in paths
    assert "/custom/upload-archive" in paths
    assert "/custom/compare" in paths
    assert "/custom/media/images/{image_id}" in paths


def test_custom_health_route() -> None:
    response = TestClient(app).get("/custom/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_observability_route_reports_phoenix_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        routes,
        "get_settings",
        lambda: Settings(
            seekdb_path=tmp_path / "seekdb",
            seekdb_db_name="test",
            image_table_name="images",
            embedding_type="siliconflow",
            embedding_api_key="test",
            embedding_base_url="https://example.test/v1",
            embedding_model="test",
            embedding_dimension=4,
            vlm_api_key="",
            vlm_base_url="https://example.test",
            vlm_model="qwen-vl",
            hybrid_default_mode="balanced",
            hybrid_recall_multiplier=2,
            hybrid_max_top_k=3,
            media_data_dir=tmp_path / "media",
            media_max_upload_bytes=1024,
            otel_enabled=True,
            otel_service_name="hybrid-service",
            otel_project_name="hybrid-project",
            otel_traces_endpoint="http://127.0.0.1:6006/v1/traces",
        ),
    )

    response = TestClient(app).get("/custom/observability")

    assert response.status_code == 200
    assert response.json() == {
        "otel_enabled": True,
        "otel_service_name": "hybrid-service",
        "otel_project_name": "hybrid-project",
        "otel_traces_endpoint": "http://127.0.0.1:6006/v1/traces",
        "phoenix_url": "http://127.0.0.1:6006",
        "phoenix_seekdb_url": "mysql://127.0.0.1:2884/phoenix",
        "start_command": "agentseek task phoenix",
    }


def test_compare_rejects_empty_query(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(routes, "get_settings", lambda: settings_for(tmp_path))

    response = TestClient(app).get("/custom/compare", params={"query": "   ", "top_k": 5})

    assert response.status_code == 400


def test_compare_clamps_top_k(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeStore:
        seen_top_k: int | None = None

        def __init__(self, **kwargs) -> None:
            pass

        def compare_modes(self, query: str, top_k: int):
            self.__class__.seen_top_k = top_k
            return {"balanced": {"query": query, "top_k": top_k}}

    monkeypatch.setattr(routes, "get_settings", lambda: settings_for(tmp_path, max_top_k=3))
    monkeypatch.setattr(routes, "HybridImageStore", FakeStore)

    response = TestClient(app).get("/custom/compare", params={"query": "red product label", "top_k": 999})

    assert response.status_code == 200
    assert FakeStore.seen_top_k == 3


def test_upload_archive_rejects_path_traversal_filename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("ok.png", b"fake image")

    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).post(
        "/custom/upload-archive",
        files={"file": ("../escape.zip", archive.getvalue(), "application/zip")},
    )

    assert response.status_code == 400
    assert not (settings.media_data_dir / "escape.zip").exists()


def test_upload_archive_cleans_partial_extraction_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("ok.png", b"fake image")

    def fail_after_partial_extract(source: Path, target: Path, **kwargs):
        target.mkdir(parents=True)
        (target / "partial.png").write_bytes(b"partial")
        raise ValueError("bad archive")

    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    monkeypatch.setattr(routes, "extract_archive_safely", fail_after_partial_extract)

    response = TestClient(app).post(
        "/custom/upload-archive",
        files={"file": ("images.zip", archive.getvalue(), "application/zip")},
    )

    assert response.status_code == 400
    assert not list((settings.media_data_dir / "extracted").glob("**/*"))


def test_media_route_rejects_paths_outside_allowed_roots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"fake image")

    class FakeVectorStore:
        def get_by_ids(self, ids):
            from langchain_core.documents import Document

            return [Document(id="escape", page_content="", metadata={"file_path": str(outside), "file_name": "outside.png"})]

    class FakeStore:
        vector_store = FakeVectorStore()

        def __init__(self, **kwargs) -> None:
            pass

    monkeypatch.setattr(routes, "get_settings", lambda: settings_for(tmp_path))
    monkeypatch.setattr(routes, "HybridImageStore", FakeStore)

    response = TestClient(app).get("/custom/media/images/escape")

    assert response.status_code == 404
