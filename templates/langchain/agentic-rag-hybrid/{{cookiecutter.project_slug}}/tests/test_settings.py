from __future__ import annotations

from {{ cookiecutter.project_slug }}.settings import get_settings


def test_siliconflow_api_key_feeds_embedding_and_vlm(monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "shared-key")
    monkeypatch.setenv("SEEKDB_PATH", "./custom-seekdb")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("VLM_API_KEY", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_api_key == "shared-key"
    assert settings.seekdb_path.name == "custom-seekdb"
    assert settings.embedding_base_url == "https://api.siliconflow.cn/v1"
    assert settings.embedding_type == "siliconflow"
    assert settings.vlm_api_key == "shared-key"
    assert settings.vlm_base_url == "https://api.siliconflow.cn/v1"
    assert settings.embedding_model == "{{ cookiecutter.embedding_model }}"
    assert settings.vlm_model == "{{ cookiecutter.vlm_model }}"
    get_settings.cache_clear()


def test_default_runtime_paths_expand_under_home(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SEEKDB_PATH", raising=False)
    monkeypatch.delenv("MEDIA_DATA_DIR", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    runtime_root = tmp_path / ".agentseek" / "hybrid-rag" / "{{ cookiecutter.project_slug }}"
    assert settings.seekdb_path == runtime_root / "seekdb"
    assert settings.media_data_dir == runtime_root / "media"
    get_settings.cache_clear()


def test_specific_siliconflow_keys_override_shared_key(monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "shared-key")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embedding-key")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://embed.example/v1")
    monkeypatch.setenv("VLM_API_KEY", "vlm-key")
    monkeypatch.setenv("VLM_BASE_URL", "https://vlm.example/v1")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_api_key == "embedding-key"
    assert settings.embedding_base_url == "https://embed.example/v1"
    assert settings.vlm_api_key == "vlm-key"
    assert settings.vlm_base_url == "https://vlm.example/v1"
    get_settings.cache_clear()
