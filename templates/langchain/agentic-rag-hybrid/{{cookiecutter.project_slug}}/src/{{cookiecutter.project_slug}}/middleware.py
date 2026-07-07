from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage

HYBRID_MODE_GUIDANCE = """Hybrid search mode guide:
- semantic: conceptual or visual similarity, object descriptions, and "looks like" requests.
- keyword: labels, colors, brands, important nouns, and caption terms.
- exact: filenames, exact categories, product labels, legal labels, and known metadata values.
- balanced: mixed intent or unclear route.
When using hybrid_search_knowledge_base, set search_mode deliberately and explain the choice briefly."""


def _with_guidance(request: ModelRequest) -> ModelRequest:
    content_blocks = list(request.system_message.content_blocks)
    content_blocks.append({"type": "text", "text": HYBRID_MODE_GUIDANCE})
    return request.override(system_message=SystemMessage(content=content_blocks))


class HybridModeGuidance(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(_with_guidance(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(_with_guidance(request))


hybrid_mode_guidance = HybridModeGuidance()
