"""Shared embedded/server seekdb vector-store configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_oceanbase.embedding_utils import DefaultEmbeddingFunctionAdapter
from langchain_oceanbase.vectorstores import OceanbaseVectorStore

EMBEDDING_DIM = 384


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def get_vector_store(embedding_function: Any | None = None) -> OceanbaseVectorStore:
    """Create the configured store; embedded seekdb is the default."""
    mode = _env("SEEKDB_MODE", "embedded").lower()
    kwargs: dict[str, object] = {
        "embedding_function": embedding_function or DefaultEmbeddingFunctionAdapter(),
        "table_name": _env("VECTOR_TABLE_NAME", "{{ cookiecutter.vector_table_name }}"),
        "vidx_metric_type": "l2",
        "embedding_dim": EMBEDDING_DIM,
    }
    db_name = _env("SEEKDB_DB_NAME", "{{ cookiecutter.seekdb_db_name }}")
    if mode == "embedded":
        path = os.path.expanduser(
            _env(
                "SEEKDB_PATH",
                "{{ cookiecutter.seekdb_path }}",
            )
        )
        kwargs["path"] = str(Path(path))
        kwargs["connection_args"] = {"db_name": db_name}
    elif mode == "server":
        kwargs["connection_args"] = {
            "host": _env("SEEKDB_HOST", "127.0.0.1"),
            "port": _env("SEEKDB_PORT", "2881"),
            "user": _env("SEEKDB_USER", "root"),
            "password": os.getenv("SEEKDB_PASSWORD", ""),
            "db_name": db_name,
        }
    else:
        raise ValueError("SEEKDB_MODE must be either 'embedded' or 'server'.")
    return OceanbaseVectorStore(**kwargs)
