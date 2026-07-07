from __future__ import annotations

import sys
import types
from pathlib import Path

from {{ cookiecutter.project_slug }}.embeddings import EmbeddingEngine, caption_image
from {{ cookiecutter.project_slug }}.sample_pack import sample_pack_dir
from {{ cookiecutter.project_slug }}.settings import Settings


def settings_for(tmp_path: Path) -> Settings:
    return Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
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


def test_embedding_engine_sends_text_and_image_payloads_to_siliconflow(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []

    class FakeHTTPStatusError(Exception):
        pass

    class FakeResponse:
        text = "ok"

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4]}]}

    def fake_post(url: str, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse()

    monkeypatch.setitem(sys.modules, "httpx", types.SimpleNamespace(post=fake_post, HTTPStatusError=FakeHTTPStatusError))

    engine = EmbeddingEngine(settings_for(tmp_path))

    assert engine.embed_text("blue shoe with visible logo") == [0.1, 0.2, 0.3, 0.4]
    assert engine.embed_image(sample_pack_dir() / "images" / "blue-logo-sneaker.png") == [0.1, 0.2, 0.3, 0.4]

    assert calls[0]["url"] == "https://example.test/v1/embeddings"
    assert calls[0]["headers"]["Authorization"] == "Bearer test"
    assert calls[0]["json"]["input"] == "blue shoe with visible logo"
    image_payload = calls[1]["json"]["input"]
    assert image_payload["image"].startswith("data:image/png;base64,")
    assert calls[0]["json"]["dimensions"] == 4
    assert calls[1]["json"]["dimensions"] == 4
