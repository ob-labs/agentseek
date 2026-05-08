from __future__ import annotations

import inspect
from dataclasses import replace
from pkgutil import resolve_name
from typing import Any

from .bridge import LangchainFactoryRequest, RunnableBinding
from .errors import LangchainConfigError
from .normalize import normalize_langchain_output


def _factory_error(factory: str, message: str) -> LangchainConfigError:
    return LangchainConfigError(f"{message} (BUB_LANGCHAIN_FACTORY={factory!r})")


def _is_runnable_like(obj: object) -> bool:
    return hasattr(obj, "invoke") and hasattr(obj, "ainvoke")


def _is_factory_callable(obj: object) -> bool:
    return callable(obj) and not _is_runnable_like(obj) and not isinstance(obj, RunnableBinding)


def _ensure_request_factory(factory: Any, *, factory_spec: str) -> None:
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return
    parameters = signature.parameters
    request_parameter = parameters.get("request")
    if request_parameter is None:
        raise _factory_error(factory_spec, "Factory must accept a `request` keyword argument")
    if request_parameter.kind not in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    ):
        raise _factory_error(factory_spec, "Factory `request` parameter must accept keyword binding")


def ensure_runnable(obj: Any, *, factory: str) -> Any:
    if not _is_runnable_like(obj):
        raise _factory_error(factory, f"Expected a Runnable with invoke/ainvoke, got {type(obj)!r}")
    return obj


def _normalize_factory_result(value: Any, *, factory: str) -> RunnableBinding:
    if not isinstance(value, RunnableBinding):
        raise _factory_error(factory, "Factory must return RunnableBinding")

    ensure_runnable(value.runnable, factory=factory)

    if value.output_parser is None:
        return replace(value, output_parser=normalize_langchain_output)

    if not callable(value.output_parser):
        raise _factory_error(factory, f"Expected output parser to be callable, got {type(value.output_parser)!r}")

    return value


def resolve_runnable_binding(factory: str, request: LangchainFactoryRequest) -> RunnableBinding:
    try:
        imported = resolve_name(factory)
    except ValueError as exc:
        raise _factory_error(factory, "Expected 'module:attr'") from exc
    except (ImportError, AttributeError) as exc:
        raise _factory_error(factory, f"Failed to resolve factory {factory!r}: {exc}") from exc
    if not _is_factory_callable(imported):
        raise _factory_error(factory, "BUB_LANGCHAIN_FACTORY must point to a callable factory")
    _ensure_request_factory(imported, factory_spec=factory)
    value = imported(request=request)
    return _normalize_factory_result(value, factory=factory)
