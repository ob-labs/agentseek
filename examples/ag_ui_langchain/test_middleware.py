from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_normalize_output_schema() -> Any:
    path = Path(__file__).resolve().with_name("middleware.py")
    spec = importlib.util.spec_from_file_location("ag_ui_langchain_middleware_test_impl", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load middleware module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._normalize_output_schema


_normalize_output_schema = _load_normalize_output_schema()


def test_normalize_output_schema_adds_default_title() -> None:
    normalized = _normalize_output_schema({
        "type": "object",
        "properties": {"ui": {"type": "array"}},
    })

    assert normalized == {
        "title": "structured_response",
        "type": "object",
        "properties": {"ui": {"type": "array"}},
    }


def test_normalize_output_schema_parses_json_string() -> None:
    normalized = _normalize_output_schema('{"type":"object","properties":{"name":{"type":"string"}}}')

    assert normalized == {
        "title": "structured_response",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }


def test_normalize_output_schema_preserves_existing_title() -> None:
    normalized = _normalize_output_schema({
        "title": "custom_ui_response",
        "type": "object",
        "properties": {"ui": {"type": "array"}},
    })

    assert normalized is not None
    assert normalized["title"] == "custom_ui_response"
