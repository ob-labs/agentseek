from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .settings import Settings

_TRACE_BOOTSTRAPPED = False


def configure_tracing(settings: Settings) -> None:
    """Register LangChain OpenTelemetry export when Phoenix tracing is enabled."""

    global _TRACE_BOOTSTRAPPED

    if _TRACE_BOOTSTRAPPED or not settings.otel_enabled:
        return

    endpoint = settings.otel_traces_endpoint.strip()
    if not endpoint:
        return

    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from openinference.semconv.resource import ResourceAttributes
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:  # pragma: no cover - exercised only in misconfigured installs
        msg = (
            "Phoenix tracing requires openinference and OpenTelemetry packages. "
            "Run `uv sync` from the generated project root."
        )
        raise RuntimeError(msg) from exc

    service_name = settings.otel_service_name.strip() or "{{ cookiecutter.project_slug }}"
    project_name = settings.otel_project_name.strip() or service_name
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            ResourceAttributes.PROJECT_NAME: project_name,
        })
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    LangChainInstrumentor().instrument(tracer_provider=provider)
    _TRACE_BOOTSTRAPPED = True


class _NoopSpan:
    def set_attribute(self, key: str, value: object) -> None:
        return None


def _set_span_attribute(span: Any, key: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, str | bool | int | float):
        span.set_attribute(key, value)
        return
    span.set_attribute(key, str(value))


@contextmanager
def trace_custom_route(
    settings: Settings,
    name: str,
    attributes: dict[str, object] | None = None,
) -> Iterator[Any]:
    """Create a Phoenix span for custom FastAPI routes when tracing is enabled."""

    if not settings.otel_enabled:
        yield _NoopSpan()
        return

    configure_tracing(settings)

    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    tracer = trace.get_tracer("{{ cookiecutter.project_slug }}.custom_routes")
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            _set_span_attribute(span, key, value)
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
