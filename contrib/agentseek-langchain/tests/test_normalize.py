from __future__ import annotations

from types import SimpleNamespace

from agentseek_langchain.normalize import to_input, to_record, to_text


def test_to_text_reads_message_like_object() -> None:
    message = SimpleNamespace(content="hello")
    assert to_text(message) == "hello"


def test_to_text_reads_last_message_content() -> None:
    payload = {
        "messages": [
            {"content": "alpha"},
            {"content": [{"text": "beta"}]},
        ]
    }
    assert to_text(payload) == "beta"


def test_to_text_prefers_final_answer_keys() -> None:
    payload = {
        "answer": {
            "content": "final answer",
        },
        "messages": [{"content": "intermediate"}],
    }
    assert to_text(payload) == "final answer"


def test_to_record_preserves_mapping_structure() -> None:
    payload = {
        "messages": [
            SimpleNamespace(content="alpha"),
            {"content": [{"text": "beta"}]},
        ],
        "meta": SimpleNamespace(content="gamma"),
    }

    assert to_record(payload) == {
        "messages": ["alpha", {"content": [{"text": "beta"}]}],
        "meta": "gamma",
    }


def test_to_input_wraps_prompt_like_values() -> None:
    prompt = [{"type": "text", "text": "hello"}, {"type": "image_url", "image_url": {"url": "x"}}]
    assert to_input(prompt) == {"messages": [{"role": "user", "content": "hello"}]}


def test_to_input_preserves_structured_dicts() -> None:
    payload = {"messages": [SimpleNamespace(content="hello")], "context": {"mode": "fast"}}
    assert to_input(payload) == {"messages": ["hello"], "context": {"mode": "fast"}}
