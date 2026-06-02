"""Minimal LangChain app that exports OTEL traces to Jaeger."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel, Field

try:
    from .settings import get_langchain_otel_sidecar_settings
except ImportError:
    from settings import get_langchain_otel_sidecar_settings

_TRACE_BOOTSTRAPPED = False


def assess_rollout_risk(change: str) -> str:
    """Return a concise rollout-risk summary for the requested change."""

    cleaned = change.strip()
    if not cleaned:
        return "No change description provided."
    return (
        f"Risk summary for {cleaned}:\n"
        "1. Validate the fallback path before rollout.\n"
        "2. Watch error rate, latency, and saturation together.\n"
        "3. Keep a one-command rollback ready for the first release window."
    )


def list_observability_checks(service_name: str) -> str:
    """Return a short checklist of production observability checks."""

    cleaned = service_name.strip() or "the service"
    return (
        f"Observability checklist for {cleaned}:\n"
        "- Confirm request volume and success rate baselines.\n"
        "- Compare p95 latency before and after the change.\n"
        "- Verify logs, traces, and feature-flag metrics line up."
    )


def _configure_tracing() -> None:
    global _TRACE_BOOTSTRAPPED

    if _TRACE_BOOTSTRAPPED:
        return

    settings = get_langchain_otel_sidecar_settings()
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": settings.service_name,
            "deployment.environment": "demo",
        })
    )
    exporter = OTLPSpanExporter(endpoint=settings.otlp_traces_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    LangchainInstrumentor().instrument()
    _TRACE_BOOTSTRAPPED = True


def _build_agent() -> Any:
    settings = get_langchain_otel_sidecar_settings()
    settings.apply_openai_env_bridge()
    return create_agent(
        model=settings.require_model(),
        tools=[assess_rollout_risk, list_observability_checks],
        system_prompt=(
            "You are a pragmatic SRE-minded assistant. "
            "Prefer concise answers, use tools when they add structure, "
            "and keep explanations directly actionable."
        ),
    )


_configure_tracing()
_AGENT = _build_agent()

app = FastAPI(title="langchain-otel-sidecar-demo", version="0.1.0")
FastAPIInstrumentor.instrument_app(app)


class InvokeRequest(BaseModel):
    """Request body for the demo invoke endpoint."""

    prompt: str = Field(min_length=1)
    session_id: str | None = None


class InvokeResponse(BaseModel):
    """Response body returned by the demo invoke endpoint."""

    reply: str
    trace_id: str
    service_name: str


def _render_content(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [_render_content(item) for item in content]
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return str(content)


def _extract_reply(result: object) -> str:
    if isinstance(result, dict) and "messages" in result:
        return _extract_reply(result["messages"])
    if isinstance(result, BaseMessage):
        return _render_content(result.content)
    if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
        collected = list(result)
        for message in reversed(collected):
            if isinstance(message, BaseMessage):
                return _render_content(message.content)
            if isinstance(message, dict):
                content = message.get("content")
                if content is not None:
                    return _render_content(content)
        if not collected:
            return ""
    return str(result)


def _current_trace_id() -> str:
    span = trace.get_current_span()
    trace_id = span.get_span_context().trace_id
    return format(trace_id, "032x")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Return a basic liveness response."""

    settings = get_langchain_otel_sidecar_settings()
    return {"status": "ok", "service_name": settings.service_name}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest) -> InvokeResponse:
    """Invoke the LangChain agent and return the final reply."""

    settings = get_langchain_otel_sidecar_settings()
    config = {
        "run_name": "langchain_otel_sidecar_demo",
        "tags": ["demo", "otel", "langchain"],
        "metadata": {"session_id": request.session_id or "adhoc"},
    }

    try:
        result = await _AGENT.ainvoke(
            {"messages": [HumanMessage(content=request.prompt)]},
            config=config,
        )
    except Exception as exc:  # pragma: no cover - demo surface
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return InvokeResponse(
        reply=_extract_reply(result),
        trace_id=_current_trace_id(),
        service_name=settings.service_name,
    )
