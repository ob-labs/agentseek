from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableLambda

from .sample_pack import sample_pack_dir
from .settings import get_settings
from .store import HybridImageStore


def _compare_modes(payload: dict[str, Any]) -> dict[str, object]:
    settings = get_settings()
    return HybridImageStore(settings=settings).compare_modes(
        query=str(payload["query"]),
        top_k=int(payload["top_k"]),
    )


def _ingest_sample_pack(payload: dict[str, Any]) -> dict[str, object]:
    settings = get_settings()
    source = sample_pack_dir() / "images"
    records = HybridImageStore(settings=settings).ingest_directory(source)
    return {"indexed": len(records), "source": str(source)}


def _ingest_archive(payload: dict[str, Any]) -> dict[str, object]:
    settings = get_settings()
    directory = Path(str(payload["directory"]))
    records = HybridImageStore(settings=settings).ingest_directory(directory)
    return {"indexed": len(records), "source": str(directory)}


compare_modes_runnable = RunnableLambda(_compare_modes).with_config({"run_name": "custom.compare"})
sample_pack_ingest_runnable = RunnableLambda(_ingest_sample_pack).with_config({"run_name": "custom.sample_pack.ingest"})
archive_ingest_runnable = RunnableLambda(_ingest_archive).with_config({"run_name": "custom.upload_archive"})
