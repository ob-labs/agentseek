"""OpenTelemetry tracing bootstrap for the LangChain app."""

from __future__ import annotations

from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .settings import ProjectSettings

_TRACE_BOOTSTRAPPED = False


def configure_tracing(settings: ProjectSettings) -> None:
    """Register LangChain instrumentation and export spans to an OTLP backend."""

    global _TRACE_BOOTSTRAPPED

    if _TRACE_BOOTSTRAPPED or not settings.otel_enabled:
        return

    endpoint = settings.otel_traces_endpoint.strip()
    if not endpoint:
        return

    service_name = settings.otel_service_name.strip() or "{{ cookiecutter.project_slug }}"
    project_name = settings.otel_project_name.strip() or service_name
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                ResourceAttributes.PROJECT_NAME: project_name,
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    LangChainInstrumentor().instrument(tracer_provider=provider)
    _TRACE_BOOTSTRAPPED = True
