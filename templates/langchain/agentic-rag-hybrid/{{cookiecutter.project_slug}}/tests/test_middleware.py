from __future__ import annotations

from langchain.messages import SystemMessage

from {{ cookiecutter.project_slug }}.middleware import HYBRID_MODE_GUIDANCE, hybrid_mode_guidance


def test_hybrid_mode_guidance_names_all_modes() -> None:
    for mode in ("semantic", "keyword", "exact", "balanced"):
        assert mode in HYBRID_MODE_GUIDANCE
    assert "hybrid_search_knowledge_base" in HYBRID_MODE_GUIDANCE


def test_hybrid_mode_guidance_supports_sync_and_async_model_calls() -> None:
    class Request:
        system_message = SystemMessage(content="base")

        def override(self, **kwargs):
            clone = Request()
            clone.system_message = kwargs["system_message"]
            return clone

    def sync_handler(request):
        return request.system_message.content

    async def async_handler(request):
        return request.system_message.content

    sync_content = hybrid_mode_guidance.wrap_model_call(Request(), sync_handler)

    assert "Hybrid search mode guide" in str(sync_content)

    import asyncio

    async_content = asyncio.run(hybrid_mode_guidance.awrap_model_call(Request(), async_handler))

    assert "Hybrid search mode guide" in str(async_content)
