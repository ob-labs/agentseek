from __future__ import annotations

from types import SimpleNamespace

from agentseek_langchain.normalize import normalize_langchain_output, normalize_langchain_value, to_input


def test_normalize_str() -> None:
    assert normalize_langchain_output("hello") == "hello"


def test_normalize_message_like_object() -> None:
    message = SimpleNamespace(content="hello")
    assert normalize_langchain_output(message) == "hello"


def test_normalize_dict_messages() -> None:
    payload = {
        "messages": [
            {"content": "alpha"},
            {"content": [{"text": "beta"}]},
        ]
    }
    assert normalize_langchain_output(payload) == "beta"


def test_normalize_prefers_output_keys_before_dumping_json() -> None:
    payload = {
        "answer": {
            "content": "final answer",
        },
        "messages": [{"content": "intermediate"}],
    }
    assert normalize_langchain_output(payload) == "final answer"


def test_normalize_value_preserves_mapping_structure() -> None:
    payload = {
        "messages": [
            SimpleNamespace(content="alpha"),
            {"content": [{"text": "beta"}]},
        ],
        "meta": SimpleNamespace(content="gamma"),
    }

    assert normalize_langchain_value(payload) == {
        "messages": ["alpha", {"content": [{"text": "beta"}]}],
        "meta": "gamma",
    }


def test_to_input_wraps_prompt_like_values() -> None:
    prompt = [{"type": "text", "text": "hello"}, {"type": "image_url", "image_url": {"url": "x"}}]
    assert to_input(prompt) == {"messages": [{"role": "user", "content": "hello"}]}


def test_to_input_preserves_structured_dicts() -> None:
    payload = {"messages": [SimpleNamespace(content="hello")], "context": {"mode": "fast"}}
    assert to_input(payload) == {"messages": ["hello"], "context": {"mode": "fast"}}
