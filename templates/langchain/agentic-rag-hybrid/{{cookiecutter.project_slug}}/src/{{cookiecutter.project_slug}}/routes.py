from __future__ import annotations

import shutil
import tarfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .hybrid import clamp_top_k, normalize_query
from .media import SUPPORTED_ARCHIVE_SUFFIXES, extract_archive_safely
from .observability import trace_custom_route
from .sample_pack import sample_pack_cases, sample_pack_dir, sample_pack_manifest, sample_pack_path
from .settings import Settings, get_settings
from .store import HybridImageStore

app = FastAPI(title="{{ cookiecutter.project_name }} Custom Routes")


def _archive_suffix(filename: str | None) -> str:
    name = filename or ""
    if not name or "/" in name or "\\" in name or Path(name).is_absolute():
        raise HTTPException(status_code=400, detail="Archive filename is invalid.")
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_ARCHIVE_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported archive type: {suffix or 'none'}")
    return suffix


def _save_upload_with_limit(file: UploadFile, target: Path, max_bytes: int) -> None:
    total = 0
    with target.open("wb") as fh:
        while chunk := file.file.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Archive is too large.")
            fh.write(chunk)


def _path_is_under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _servable_image_path(raw_path: str, settings: Settings) -> Path:
    path = Path(raw_path).resolve()
    allowed_roots = (settings.media_data_dir.resolve(), sample_pack_dir().resolve())
    if not path.is_file() or not any(_path_is_under(path, root) for root in allowed_roots):
        raise HTTPException(status_code=404, detail="Image file missing")
    return path


@app.get("/custom/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/custom/observability")
def observability() -> dict[str, object]:
    settings = get_settings()
    return {
        "otel_enabled": settings.otel_enabled,
        "otel_service_name": settings.otel_service_name,
        "otel_project_name": settings.otel_project_name,
        "otel_traces_endpoint": settings.otel_traces_endpoint,
        "phoenix_url": "http://127.0.0.1:6006",
        "phoenix_seekdb_url": "mysql://127.0.0.1:2884/phoenix",
        "start_command": "agentseek task phoenix",
    }


@app.get("/custom/sample-pack")
def sample_pack() -> dict[str, object]:
    return {
        "manifest": sample_pack_manifest(),
        "cases": sample_pack_cases(),
        "download_url": "/custom/sample-pack/download",
    }


@app.post("/custom/sample-pack/ingest")
def ingest_sample_pack() -> dict[str, object]:
    settings = get_settings()
    with trace_custom_route(
        settings,
        "custom.sample_pack.ingest",
        {
            "agentseek.route": "/custom/sample-pack/ingest",
            "agentseek.source": "sample_pack",
        },
    ):
        records = HybridImageStore(settings=settings).ingest_directory(sample_pack_dir() / "images")
    return {"indexed": len(records), "source": str(sample_pack_dir() / "images")}


@app.get("/custom/sample-pack/download")
def download_sample_pack() -> FileResponse:
    return FileResponse(
        sample_pack_path(),
        media_type="application/zip",
        filename="sample_pack.zip",
    )


@app.post("/custom/upload-archive")
async def upload_archive(file: UploadFile = File(...)) -> dict[str, object]:
    settings = get_settings()
    upload_dir = settings.media_data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = _archive_suffix(file.filename)
    archive_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    extracted_target = settings.media_data_dir / "extracted" / archive_path.stem
    try:
        with trace_custom_route(
            settings,
            "custom.upload_archive",
            {
                "agentseek.route": "/custom/upload-archive",
                "agentseek.archive_suffix": suffix,
            },
        ):
            _save_upload_with_limit(file, archive_path, settings.media_max_upload_bytes)
            extracted = extract_archive_safely(
                archive_path,
                extracted_target,
                max_member_bytes=settings.media_max_upload_bytes,
                max_total_bytes=settings.media_max_upload_bytes,
            )
            records = HybridImageStore(settings=settings).ingest_directory(extracted)
    except HTTPException:
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(extracted_target, ignore_errors=True)
        raise
    except (ValueError, zipfile.BadZipFile, tarfile.TarError) as exc:
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(extracted_target, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(extracted_target, ignore_errors=True)
        raise
    return {"indexed": len(records), "source": str(extracted)}


@app.get("/custom/compare")
def compare(query: str, top_k: int = 5) -> dict[str, object]:
    settings = get_settings()
    try:
        normalized_query = normalize_query(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    clamped_top_k = clamp_top_k(top_k, settings.hybrid_max_top_k)
    with trace_custom_route(
        settings,
        "custom.compare",
        {
            "agentseek.route": "/custom/compare",
            "agentseek.query": normalized_query,
            "agentseek.top_k": clamped_top_k,
            "agentseek.modes": "balanced,semantic,keyword,exact",
        },
    ):
        traces = HybridImageStore(settings=settings).compare_modes(
            query=normalized_query,
            top_k=clamped_top_k,
        )
    return {mode: trace for mode, trace in traces.items()}


@app.get("/custom/media/images/{image_id}")
def image(image_id: str) -> FileResponse:
    settings = get_settings()
    store = HybridImageStore(settings=settings)
    docs = store.vector_store.get_by_ids([image_id])
    if not docs:
        raise HTTPException(status_code=404, detail="Image not found")
    file_path = _servable_image_path(docs[0].metadata.get("file_path", ""), settings)
    return FileResponse(file_path)
