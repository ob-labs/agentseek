from __future__ import annotations

import re
import shutil
import tarfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .hybrid import clamp_top_k, normalize_query
from .media import SUPPORTED_ARCHIVE_SUFFIXES, SUPPORTED_IMAGE_SUFFIXES, extract_archive_safely
from .observability import configure_tracing
from .retrieval_runnables import archive_ingest_runnable, compare_modes_runnable, sample_pack_ingest_runnable
from .sample_pack import sample_pack_cases, sample_pack_manifest, sample_pack_path
from .settings import Settings, get_settings

app = FastAPI(title="{{ cookiecutter.project_name }} Custom Routes")
IMAGE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


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


def _managed_image_path(image_id: str, settings: Settings) -> Path:
    if not IMAGE_ID_PATTERN.fullmatch(image_id):
        raise HTTPException(status_code=404, detail="Image not found")

    image_dir = settings.media_data_dir / "images"
    if image_dir.is_symlink():
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        media_root = settings.media_data_dir.resolve()
        image_root = image_dir.resolve()
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=404, detail="Image not found") from exc

    if not image_root.is_dir() or not _path_is_under(image_root, media_root):
        raise HTTPException(status_code=404, detail="Image not found")

    matches: list[Path] = []
    for candidate in image_root.iterdir():
        if (
            candidate.stem != image_id
            or candidate.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES
            or candidate.is_symlink()
        ):
            continue
        try:
            resolved = candidate.resolve()
        except (OSError, RuntimeError):
            continue
        if resolved.is_file() and _path_is_under(resolved, image_root):
            matches.append(resolved)

    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="Image not found")
    return matches[0]


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
    configure_tracing(settings)
    return sample_pack_ingest_runnable.invoke({})


@app.get("/custom/sample-pack/download")
def download_sample_pack() -> FileResponse:
    return FileResponse(
        sample_pack_path(),
        media_type="application/zip",
        filename="sample_pack.zip",
    )


@app.post("/custom/upload-archive")
def upload_archive(file: UploadFile = File(...)) -> dict[str, object]:
    settings = get_settings()
    upload_dir = settings.media_data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = _archive_suffix(file.filename)
    archive_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    extracted_target = settings.media_data_dir / "extracted" / archive_path.stem
    try:
        _save_upload_with_limit(file, archive_path, settings.media_max_upload_bytes)
        extract_archive_safely(
            archive_path,
            extracted_target,
            max_member_bytes=settings.media_max_upload_bytes,
            max_total_bytes=settings.media_max_upload_bytes,
        )
        configure_tracing(settings)
        result = archive_ingest_runnable.invoke({"directory": str(extracted_target)})
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
    return result


@app.get("/custom/compare")
def compare(query: str, top_k: int = 5) -> dict[str, object]:
    settings = get_settings()
    try:
        normalized_query = normalize_query(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    clamped_top_k = clamp_top_k(top_k, settings.hybrid_max_top_k)
    configure_tracing(settings)
    traces = compare_modes_runnable.invoke({"query": normalized_query, "top_k": clamped_top_k})
    return {mode: trace for mode, trace in traces.items()}


@app.get("/custom/media/images/{image_id}")
def image(image_id: str) -> FileResponse:
    settings = get_settings()
    return FileResponse(_managed_image_path(image_id, settings))
