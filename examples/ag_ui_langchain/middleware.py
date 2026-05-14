"""CopilotKit ↔ LangChain middleware (aligned with LangChain CopilotKit docs).

See: https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from langchain.agents.middleware import before_agent, wrap_model_call
from langchain.agents.structured_output import ProviderStrategy

_DEFAULT_OUTPUT_SCHEMA_TITLE = "structured_response"


@wrap_model_call
async def apply_structured_output_schema(request, handler):
    schema: object = None
    runtime = getattr(request, "runtime", None)
    runtime_context = getattr(runtime, "context", None)

    if isinstance(runtime_context, Mapping):
        schema = runtime_context.get("output_schema")

    if schema is None and isinstance(getattr(request, "state", None), dict):
        copilot_context = request.state.get("copilotkit", {}).get("context")
        if isinstance(copilot_context, list):
            for item in copilot_context:
                if isinstance(item, dict) and item.get("description") == "output_schema":
                    schema = item.get("value")
                    break

    normalized_schema = _normalize_output_schema(schema)
    if normalized_schema is not None:
        request = request.override(
            response_format=ProviderStrategy(schema=normalized_schema, strict=True),
        )

    return await handler(request)


@before_agent
def normalize_context(state, runtime):
    copilotkit_state = state.get("copilotkit", {})
    context = copilotkit_state.get("context")

    if isinstance(context, list):
        normalized = [item.model_dump() if hasattr(item, "model_dump") else item for item in context]
        return {"copilotkit": {**copilotkit_state, "context": normalized}}

    return None


def _normalize_output_schema(schema: object) -> dict[str, Any] | None:
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError:
            return None

    if not isinstance(schema, Mapping):
        return None

    normalized = dict(schema)
    title = normalized.get("title")
    if not isinstance(title, str) or not title.strip():
        normalized["title"] = _DEFAULT_OUTPUT_SCHEMA_TITLE
    return normalized
