from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return int(value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    seekdb_path: Path
    seekdb_db_name: str
    image_table_name: str
    embedding_type: str
    embedding_api_key: str
    embedding_base_url: str
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
    otel_enabled: bool = False
    otel_service_name: str = "{{ cookiecutter.project_slug }}"
    otel_project_name: str = "{{ cookiecutter.project_slug }}"
    otel_traces_endpoint: str = "http://127.0.0.1:6006/v1/traces"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY", "")
    return Settings(
        seekdb_path=Path(os.getenv("SEEKDB_PATH", "{{ cookiecutter.seekdb_path }}")).expanduser().resolve(),
        seekdb_db_name=os.getenv("SEEKDB_DB_NAME", "{{ cookiecutter.seekdb_db_name }}"),
        image_table_name=os.getenv("IMAGE_TABLE_NAME", "{{ cookiecutter.image_table_name }}"),
        embedding_type=os.getenv("EMBEDDING_TYPE", "siliconflow"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY") or siliconflow_api_key,
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "{{ cookiecutter.embedding_model }}"),
        embedding_dimension=_int_env("EMBEDDING_DIMENSION", {{ cookiecutter.embedding_dimension }}),
        vlm_api_key=os.getenv("VLM_API_KEY") or siliconflow_api_key,
        vlm_base_url=os.getenv("VLM_BASE_URL", "https://api.siliconflow.cn/v1"),
        vlm_model=os.getenv("VLM_MODEL", "{{ cookiecutter.vlm_model }}"),
        hybrid_default_mode=os.getenv("HYBRID_DEFAULT_MODE", "balanced"),
        hybrid_recall_multiplier=_int_env("HYBRID_RECALL_MULTIPLIER", 5),
        hybrid_max_top_k=_int_env("HYBRID_MAX_TOP_K", 20),
        media_data_dir=Path(os.getenv("MEDIA_DATA_DIR", "{{ cookiecutter.media_data_dir }}")).expanduser().resolve(),
        media_max_upload_bytes=_int_env("MEDIA_MAX_UPLOAD_MB", 50) * 1024 * 1024,
        otel_enabled=_bool_env("AGENTSEEK_OTEL_ENABLED", False),
        otel_service_name=os.getenv("AGENTSEEK_OTEL_SERVICE_NAME", "{{ cookiecutter.project_slug }}"),
        otel_project_name=os.getenv("AGENTSEEK_OTEL_PROJECT_NAME", "{{ cookiecutter.project_slug }}"),
        otel_traces_endpoint=os.getenv(
            "AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "http://127.0.0.1:6006/v1/traces",
        ),
    )
