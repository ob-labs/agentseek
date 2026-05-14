from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, TypeGuard

type ObjectDict = dict[str, object]
type StrMapping = Mapping[str, object]
type MessagePart = str | dict[str, object]
type HumanMessageContent = str | list[MessagePart]


class SupportsModelDump(Protocol):
    def model_dump(self) -> object: ...


def supports_model_dump(value: object) -> TypeGuard[SupportsModelDump]:
    return callable(getattr(value, "model_dump", None))


def is_str_mapping(value: object) -> TypeGuard[StrMapping]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


def as_str_mapping(value: object) -> StrMapping | None:
    return value if is_str_mapping(value) else None


def copy_str_mapping(value: object) -> ObjectDict | None:
    mapping = as_str_mapping(value)
    if mapping is None:
        return None
    return {key: mapping[key] for key in mapping}


def model_dump_or_none(value: object) -> object | None:
    if not supports_model_dump(value):
        return None
    return value.model_dump()
