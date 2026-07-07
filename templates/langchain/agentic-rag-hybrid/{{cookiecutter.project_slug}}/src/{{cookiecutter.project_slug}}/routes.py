from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .media import extract_archive_safely
from .sample_pack import sample_pack_cases, sample_pack_dir, sample_pack_manifest, sample_pack_path
from .settings import get_settings
from .store import HybridImageStore

app = FastAPI(title="{{ cookiecutter.project_name }} Custom Routes")


@app.get("/custom/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/custom/sample-pack")
def sample_pack() -> dict[str, object]:
    return {
        "manifest": sample_pack_manifest(),
        "cases": sample_pack_cases(),
        "download_url": "/custom/sample-pack/download",
    }


@app.post("/custom/sample-pack/ingest")
def ingest_sample_pack() -> dict[str, object]:
    records = HybridImageStore().ingest_directory(sample_pack_dir() / "images")
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
    archive_path = upload_dir / (file.filename or "images.zip")
    with archive_path.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    extracted = extract_archive_safely(
        archive_path,
        settings.media_data_dir / "extracted" / archive_path.stem,
    )
    records = HybridImageStore().ingest_directory(extracted)
    return {"indexed": len(records), "source": str(extracted)}


@app.get("/custom/compare")
def compare(query: str, top_k: int = 5) -> dict[str, object]:
    traces = HybridImageStore().compare_modes(query=query, top_k=top_k)
    return {mode: trace for mode, trace in traces.items()}


@app.get("/custom/media/images/{image_id}")
def image(image_id: str) -> FileResponse:
    store = HybridImageStore()
    result = store.collection.get(ids=[image_id], include=["metadatas"])
    metadatas = result.get("metadatas", [])
    if not metadatas:
        raise HTTPException(status_code=404, detail="Image not found")
    file_path = Path(metadatas[0].get("file_path", ""))
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(file_path)
