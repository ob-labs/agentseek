from __future__ import annotations

import sys
import types
from pathlib import Path

from {{ cookiecutter.project_slug }}.embeddings import caption_image
from {{ cookiecutter.project_slug }}.settings import Settings


def settings_for(tmp_path: Path) -> Settings:
    return Settings(
        seekdb_host="127.0.0.1",
        seekdb_port="2881",
        seekdb_user="root",
        seekdb_password="",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="dashscope",
        embedding_api_key="test",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="test-key",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=3,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )


def test_caption_image_uses_actual_image_mime_type(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = types.SimpleNamespace(content="caption")
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            pass

        chat = types.SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    image = tmp_path / "label.png"
    image.write_bytes(b"fake png")

    assert caption_image(image, settings_for(tmp_path)) == "caption"

    content = captured["messages"][0]["content"]
    image_url = content[1]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")
