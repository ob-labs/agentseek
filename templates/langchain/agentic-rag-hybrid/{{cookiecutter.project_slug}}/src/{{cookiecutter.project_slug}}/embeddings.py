from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from .settings import Settings, get_settings


class EmbeddingEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def embed_image(self, image_path: Path) -> list[float]:
        if self.settings.embedding_type != "siliconflow":
            raise ValueError(f"Unsupported EMBEDDING_TYPE: {self.settings.embedding_type}")
        return self._embed_siliconflow({"image": self._data_uri(image_path)})

    def embed_text(self, text: str) -> list[float]:
        if self.settings.embedding_type != "siliconflow":
            raise ValueError(f"Unsupported EMBEDDING_TYPE: {self.settings.embedding_type}")
        return self._embed_siliconflow(text)

    def _embed_siliconflow(self, input_payload: str | dict[str, Any]) -> list[float]:
        if not self.settings.embedding_api_key:
            raise RuntimeError("AGENTSEEK_API_KEY or EMBEDDING_API_KEY is required for SiliconFlow embeddings.")

        import httpx

        payload: dict[str, Any] = {
            "model": self.settings.embedding_model,
            "input": input_payload,
            "encoding_format": "float",
        }
        if self.settings.embedding_dimension > 0:
            payload["dimensions"] = self.settings.embedding_dimension
        response = httpx.post(
            f"{self.settings.embedding_base_url.rstrip('/')}/embeddings",
            headers={
                "Authorization": f"Bearer {self.settings.embedding_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"SiliconFlow embedding failed: {response.text}") from exc
        data = response.json()
        return list(data["data"][0]["embedding"])

    @staticmethod
    def _data_uri(path: Path) -> str:
        suffix = path.suffix.lower().lstrip(".")
        mime_suffix = "jpeg" if suffix == "jpg" else suffix
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:image/{mime_suffix};base64,{encoded}"


def caption_image(image_path: Path, settings: Settings | None = None) -> str:
    current = settings or get_settings()
    if not current.vlm_api_key:
        return "[VLM_API_KEY not set; caption unavailable]"
    import openai

    client = openai.OpenAI(api_key=current.vlm_api_key, base_url=current.vlm_base_url)
    response = client.chat.completions.create(
        model=current.vlm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe the main visible object, category, colors, and any readable labels in one concise sentence.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": EmbeddingEngine._data_uri(image_path)},
                    },
                ],
            }
        ],
        temperature=0.1,
    )
    content = response.choices[0].message.content
    return content.strip() if content else "[No caption]"
