from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    seekdb_host: str
    seekdb_port: str
    seekdb_user: str
    seekdb_password: str
    seekdb_db_name: str
    image_table_name: str
    embedding_type: str
    embedding_api_key: str
    embedding_model: str
    embedding_dimension: int
    vlm_api_key: str
    vlm_base_url: str
    vlm_model: str
    hybrid_default_mode: str
    hybrid_recall_multiplier: int
    hybrid_max_top_k: int
    media_data_dir: Path
    media_max_upload_bytes: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        seekdb_host=os.getenv("SEEKDB_HOST", "127.0.0.1"),
        seekdb_port=os.getenv("SEEKDB_PORT", "2881"),
        seekdb_user=os.getenv("SEEKDB_USER", "root"),
        seekdb_password=os.getenv("SEEKDB_PASSWORD", ""),
        seekdb_db_name=os.getenv("SEEKDB_DB_NAME", "{{ cookiecutter.seekdb_db_name }}"),
        image_table_name=os.getenv("IMAGE_TABLE_NAME", "{{ cookiecutter.image_table_name }}"),
        embedding_type=os.getenv("EMBEDDING_TYPE", "dashscope"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "{{ cookiecutter.embedding_model }}"),
        embedding_dimension=_int_env("EMBEDDING_DIMENSION", {{ cookiecutter.embedding_dimension }}),
        vlm_api_key=os.getenv("VLM_API_KEY", ""),
        vlm_base_url=os.getenv("VLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        vlm_model=os.getenv("VLM_MODEL", "{{ cookiecutter.vlm_model }}"),
        hybrid_default_mode=os.getenv("HYBRID_DEFAULT_MODE", "balanced"),
        hybrid_recall_multiplier=_int_env("HYBRID_RECALL_MULTIPLIER", 5),
        hybrid_max_top_k=_int_env("HYBRID_MAX_TOP_K", 20),
        media_data_dir=Path(os.getenv("MEDIA_DATA_DIR", "./data")).resolve(),
        media_max_upload_bytes=_int_env("MEDIA_MAX_UPLOAD_MB", 50) * 1024 * 1024,
    )
