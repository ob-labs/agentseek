from __future__ import annotations

import inspect
import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from {{ cookiecutter.project_slug }} import routes
from {{ cookiecutter.project_slug }}.routes import app
from {{ cookiecutter.project_slug }}.settings import Settings
from {{ cookiecutter.project_slug }}.store import _image_id


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
    class FakeRunnable:
        seen_payload: dict[str, object] | None = None

        def invoke(self, payload: dict[str, object]):
            self.seen_payload = payload
            return {"balanced": {"query": payload["query"], "top_k": payload["top_k"]}}

    monkeypatch.setattr(routes, "get_settings", lambda: settings_for(tmp_path, max_top_k=3))
    monkeypatch.setattr(routes, "configure_tracing", lambda settings: None)
    fake_runnable = FakeRunnable()
    monkeypatch.setattr(routes, "compare_modes_runnable", fake_runnable)

    response = TestClient(app).get("/custom/compare", params={"query": "red product label", "top_k": 999})

    assert response.status_code == 200
    assert fake_runnable.seen_payload == {"query": "red product label", "top_k": 3}


def test_compare_route_invokes_langchain_runnable_for_phoenix_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path, max_top_k=3)
    configured: list[Settings] = []

    class FakeRunnable:
        seen_payload: dict[str, object] | None = None

        def invoke(self, payload: dict[str, object]):
            self.seen_payload = payload
            return {"keyword": {"query": payload["query"], "top_k": payload["top_k"]}}

    fake_runnable = FakeRunnable()

    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    monkeypatch.setattr(routes, "configure_tracing", configured.append)
    monkeypatch.setattr(routes, "compare_modes_runnable", fake_runnable)

    response = TestClient(app).get("/custom/compare", params={"query": "red tea label", "top_k": 999})

    assert response.status_code == 200
    assert configured == [settings]
    assert fake_runnable.seen_payload == {"query": "red tea label", "top_k": 3}


def test_ingest_sample_pack_route_invokes_langchain_runnable_for_phoenix_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    configured: list[Settings] = []

    class FakeRunnable:
        seen_payload: dict[str, object] | None = None

        def invoke(self, payload: dict[str, object]):
            self.seen_payload = payload
            return {"indexed": 2, "source": "sample-pack"}

    fake_runnable = FakeRunnable()

    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    monkeypatch.setattr(routes, "configure_tracing", configured.append)
    monkeypatch.setattr(routes, "sample_pack_ingest_runnable", fake_runnable)

    response = TestClient(app).post("/custom/sample-pack/ingest")

    assert response.status_code == 200
    assert response.json() == {"indexed": 2, "source": "sample-pack"}
    assert configured == [settings]
    assert fake_runnable.seen_payload == {}


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


def test_upload_archive_route_invokes_langchain_runnable_for_phoenix_trace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    configured: list[Settings] = []
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("ok.png", b"fake image")

    def extract_archive(source: Path, target: Path, **kwargs):
        target.mkdir(parents=True)
        (target / "ok.png").write_bytes(b"fake image")
        return [target / "ok.png"]

    class FakeRunnable:
        seen_payload: dict[str, object] | None = None

        def invoke(self, payload: dict[str, object]):
            self.seen_payload = payload
            return {"indexed": 1, "source": payload["directory"]}

    fake_runnable = FakeRunnable()

    monkeypatch.setattr(routes, "get_settings", lambda: settings)
    monkeypatch.setattr(routes, "configure_tracing", configured.append)
    monkeypatch.setattr(routes, "extract_archive_safely", extract_archive)
    monkeypatch.setattr(routes, "archive_ingest_runnable", fake_runnable)

    response = TestClient(app).post(
        "/custom/upload-archive",
        files={"file": ("images.zip", archive.getvalue(), "application/zip")},
    )

    assert response.status_code == 200
    assert response.json()["indexed"] == 1
    assert configured == [settings]
    assert fake_runnable.seen_payload is not None
    assert Path(str(fake_runnable.seen_payload["directory"])).parent == settings.media_data_dir / "extracted"


def test_upload_archive_runs_in_fastapi_threadpool() -> None:
    assert not inspect.iscoroutinefunction(routes.upload_archive)


def test_media_route_rejects_files_outside_managed_image_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"fake image")

    monkeypatch.setattr(routes, "get_settings", lambda: settings_for(tmp_path))

    response = TestClient(app).get("/custom/media/images/escape")

    assert response.status_code == 404


def test_media_route_serves_managed_file_for_fragment_like_source_stem(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    source_image = tmp_path / "front#1.png"
    image_id = _image_id(source_image)
    managed_path = settings.media_data_dir / "images" / f"{image_id}.png"
    managed_path.parent.mkdir(parents=True)
    managed_path.write_bytes(b"managed image")

    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    image_url = f"/custom/media/images/{image_id}"
    assert "#" not in image_url
    assert "?" not in image_url

    response = TestClient(app).get(image_url)

    assert response.status_code == 200
    assert response.content == b"managed image"


def test_media_route_rejects_unsafe_image_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/bad$id")

    assert response.status_code == 404

    with pytest.raises(routes.HTTPException) as exc_info:
        routes._managed_image_path("../outside", settings)

    assert exc_info.value.status_code == 404


def test_media_route_rejects_symlinked_image_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    (outside_root / "escape.png").write_bytes(b"outside image")
    settings.media_data_dir.mkdir(parents=True)
    (settings.media_data_dir / "images").symlink_to(outside_root, target_is_directory=True)
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/escape")

    assert response.status_code == 404


def test_media_route_rejects_symlinked_image_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    image_root = settings.media_data_dir / "images"
    image_root.mkdir(parents=True)
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside image")
    (image_root / "escape.png").symlink_to(outside)
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/escape")

    assert response.status_code == 404


def test_media_route_rejects_symlink_loop_as_image_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    settings.media_data_dir.mkdir(parents=True)
    image_root = settings.media_data_dir / "images"
    image_root.symlink_to(image_root, target_is_directory=True)
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/loop")

    assert response.status_code == 404


def test_media_route_rejects_symlink_loop_as_image_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    image_root = settings.media_data_dir / "images"
    image_root.mkdir(parents=True)
    candidate = image_root / "loop.png"
    candidate.symlink_to(candidate)
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/loop")

    assert response.status_code == 404


def test_media_route_rejects_ambiguous_duplicate_stems(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    image_root = settings.media_data_dir / "images"
    image_root.mkdir(parents=True)
    (image_root / "duplicate.png").write_bytes(b"png image")
    (image_root / "duplicate.jpg").write_bytes(b"jpg image")
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get("/custom/media/images/duplicate")

    assert response.status_code == 404


def test_media_route_accepts_valid_image_id_characters(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = settings_for(tmp_path)
    image_id = "A1.uuid_like-name_part"
    managed_path = settings.media_data_dir / "images" / f"{image_id}.webp"
    managed_path.parent.mkdir(parents=True)
    managed_path.write_bytes(b"managed image")
    monkeypatch.setattr(routes, "get_settings", lambda: settings)

    response = TestClient(app).get(f"/custom/media/images/{image_id}")

    assert response.status_code == 200
    assert response.content == b"managed image"
