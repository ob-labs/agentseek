from __future__ import annotations

from fastapi.testclient import TestClient

from {{ cookiecutter.project_slug }}.routes import app


def test_custom_route_paths_are_mounted_under_custom_prefix() -> None:
    paths = {route.path for route in app.routes}
    assert "/custom/health" in paths
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
