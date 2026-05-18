from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Callable, Iterator, Sized
from dataclasses import dataclass, field
from typing import Any

PATCH_MARKER = "__agentseek_observability_wrapped__"


def _unwrap_descriptor(descriptor: Any) -> Any:
    if isinstance(descriptor, classmethod | staticmethod):
        return descriptor.__func__
    return descriptor


@dataclass
class PatchRegistry:
    _patched: list[tuple[object, str, Any]] = field(default_factory=list)

    def patch(
        self, target: object, attr: str, wrapper_factory: Callable[[Callable[..., Any]], Callable[..., Any]]
    ) -> None:
        descriptor = inspect.getattr_static(target, attr)
        original = _unwrap_descriptor(descriptor)
        if getattr(original, PATCH_MARKER, False):
            return

        wrapped = wrapper_factory(original)
        setattr(wrapped, PATCH_MARKER, True)

        if isinstance(descriptor, classmethod):
            replacement: Any = classmethod(wrapped)
        elif isinstance(descriptor, staticmethod):
            replacement = staticmethod(wrapped)
        else:
            replacement = wrapped

        self._patched.append((target, attr, descriptor))
        setattr(target, attr, replacement)

    def restore(self) -> None:
        for target, attr, descriptor in reversed(self._patched):
            setattr(target, attr, descriptor)
        self._patched.clear()


@dataclass
class InstrumentationHandle:
    patches: PatchRegistry

    def close(self) -> None:
        self.patches.restore()


def safe_count(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, Sized):
        return len(value)  # type: ignore[arg-type]
    return 1


def close_span(span_cm: Any, error: BaseException | None = None) -> None:
    if error is None:
        span_cm.__exit__(None, None, None)
        return
    span_cm.__exit__(type(error), error, error.__traceback__)


def wrap_iterator_with_span[T](
    iterator: Iterator[T],
    span_cm: Any,
    *,
    on_finish: Callable[[Any], None] | None = None,
) -> Iterator[T]:
    span = span_cm.__enter__()
    error: BaseException | None = None
    try:
        yield from iterator
    except BaseException as exc:
        error = exc
        raise
    finally:
        if on_finish is not None:
            on_finish(span)
        close_span(span_cm, error)


async def wrap_async_iterator_with_span[T](
    iterator: AsyncIterator[T],
    span_cm: Any,
    *,
    on_finish: Callable[[Any], None] | None = None,
) -> AsyncIterator[T]:
    span = span_cm.__enter__()
    error: BaseException | None = None
    try:
        async for item in iterator:
            yield item
    except BaseException as exc:
        error = exc
        raise
    finally:
        if on_finish is not None:
            on_finish(span)
        close_span(span_cm, error)
