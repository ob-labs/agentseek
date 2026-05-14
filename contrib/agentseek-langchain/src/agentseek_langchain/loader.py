from __future__ import annotations

import importlib
from typing import Any

from agentseek_langchain.spec import RunnableSpec


def load_spec_from_path(path: str) -> RunnableSpec:
    module_name, separator, symbol_name = path.partition(":")
    if not separator or not module_name or not symbol_name:
        raise ValueError("LangChain spec path must look like 'module.submodule:SYMBOL'")
    module = importlib.import_module(module_name)
    try:
        exported = getattr(module, symbol_name)
    except AttributeError as exc:
        raise AttributeError(f"Cannot find symbol {symbol_name!r} in module {module_name!r}") from exc
    return resolve_spec(exported)


def resolve_spec(exported: Any) -> RunnableSpec:
    if isinstance(exported, RunnableSpec):
        return exported
    if callable(exported) and not _looks_like_runnable(exported):
        produced = exported()
        if isinstance(produced, RunnableSpec):
            return produced
        raise TypeError("LangChain spec factory must return RunnableSpec")
    raise TypeError("LangChain spec export must be RunnableSpec or zero-argument factory returning RunnableSpec")


def _looks_like_runnable(value: object) -> bool:
    return hasattr(value, "invoke") or hasattr(value, "ainvoke")
