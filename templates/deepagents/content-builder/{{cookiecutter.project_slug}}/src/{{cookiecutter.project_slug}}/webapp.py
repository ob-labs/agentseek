"""Custom FastAPI routes for serving generated images.

Mounted via ``langgraph.json`` ``http.app`` so the frontend can display
blog covers and social images at ``/images/<relative-path>``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@app.get("/images/{path:path}")
def serve_image(path: str):
    """Serve a generated image file by its relative path under the project root."""
    file_path = (PROJECT_ROOT / path).resolve()
    if not file_path.is_relative_to(PROJECT_ROOT):
        return JSONResponse({"error": "Invalid path"}, status_code=400)
    suffix = file_path.suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        return JSONResponse({"error": "Not an image"}, status_code=400)
    if not file_path.is_file():
        return JSONResponse({"error": "Not found"}, status_code=404)
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }[suffix]
    return FileResponse(file_path, media_type=media_type)
