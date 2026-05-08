from __future__ import annotations

from dataclasses import replace
from pkgutil import resolve_name
from typing import Any

from .bridge import LangchainFactoryRequest, RunnableBinding
from .errors import LangchainConfigError
from .normalize import to_text


def _factory_error(factory: str, message: str) -> LangchainConfigError:
    return LangchainConfigError(f"{message} (BUB_LANGCHAIN_FACTORY={factory!r})")


def _normalize_factory_result(value: Any, *, factory: str) -> RunnableBinding:
    if not isinstance(value, RunnableBinding):
        raise _factory_error(factory, "Factory must return RunnableBinding")

    if not hasattr(value.runnable, "invoke") or not hasattr(value.runnable, "ainvoke"):
        raise _factory_error(factory, f"Expected a Runnable with invoke/ainvoke, got {type(value.runnable)!r}")

    if value.output_parser is None:
        return replace(
            value,
            output_parser=to_text,
            stream_parser=to_text,
        )

    if not callable(value.output_parser):
        raise _factory_error(factory, f"Expected output parser to be callable, got {type(value.output_parser)!r}")

    if value.stream_parser is not None and not callable(value.stream_parser):
        raise _factory_error(factory, f"Expected stream parser to be callable, got {type(value.stream_parser)!r}")

    return value


def resolve_runnable_binding(factory: str, request: LangchainFactoryRequest) -> RunnableBinding:
    try:
        imported = resolve_name(factory)
    except ValueError as exc:
        raise _factory_error(factory, "Expected 'module:attr'") from exc
    except (ImportError, AttributeError) as exc:
        raise _factory_error(factory, f"Failed to resolve factory {factory!r}: {exc}") from exc
    if not callable(imported) or (hasattr(imported, "invoke") and hasattr(imported, "ainvoke")):
        raise _factory_error(factory, "BUB_LANGCHAIN_FACTORY must point to a callable factory")
    value = imported(request=request)
    return _normalize_factory_result(value, factory=factory)
