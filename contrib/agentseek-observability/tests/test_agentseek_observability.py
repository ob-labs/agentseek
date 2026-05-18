from __future__ import annotations

import asyncio
import importlib
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import logfire
import pytest
from agentseek_observability.plugin import instrument_agentseek_observability
from any_llm.any_llm import AnyLLM
from bub.framework import BubFramework
from logfire.testing import IncrementalIdGenerator, TestExporter, TimeGenerator
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class FakeProvider(AnyLLM):
    PROVIDER_NAME = "fake"
    PROVIDER_DOCUMENTATION_URL = "https://example.com/fake"
    ENV_API_KEY_NAME = "FAKE_API_KEY"
    SUPPORTS_COMPLETION_STREAMING = True
    SUPPORTS_COMPLETION = True
    SUPPORTS_COMPLETION_REASONING = True
    SUPPORTS_COMPLETION_IMAGE = False
    SUPPORTS_COMPLETION_PDF = False
    SUPPORTS_EMBEDDING = False
    SUPPORTS_RESPONSES = False
    SUPPORTS_LIST_MODELS = False
    SUPPORTS_BATCH = False

    def __init__(self, script: Iterator[dict[str, Any]]) -> None:
        self._script = script
        super().__init__(api_key="test-key")

    def _verify_and_set_api_key(self, api_key: str | None = None) -> str | None:
        return api_key or "test-key"

    def _init_client(self, api_key: str | None = None, api_base: str | None = None, **kwargs: Any) -> None:
        return None

    @staticmethod
    def _convert_completion_params(params: Any, **kwargs: Any) -> dict[str, Any]:
        return {}

    @staticmethod
    def _convert_completion_response(response: Any) -> Any:
        return response

    @staticmethod
    def _convert_completion_chunk_response(response: Any, **kwargs: Any) -> Any:
        return response

    @staticmethod
    def _convert_embedding_params(params: Any, **kwargs: Any) -> dict[str, Any]:
        return {}

    @staticmethod
    def _convert_embedding_response(response: Any) -> Any:
        return response

    @staticmethod
    def _convert_list_models_response(response: Any) -> list[Any]:
        return []

    async def _acompletion(self, params, **kwargs: Any) -> Any:
        step = next(self._script)
        if step["kind"] == "stream":

            async def iterator():
                for chunk in step["chunks"]:
                    yield chunk

            return iterator()
        return step["response"]


def _load_bub_config(config_path: Path) -> None:
    configure = importlib.import_module("bub.configure")
    configure.load(config_path)


@pytest.fixture
def exporter() -> TestExporter:
    exporter = TestExporter()
    time_generator = TimeGenerator()
    logfire.configure(
        send_to_logfire=False,
        console=False,
        advanced=logfire.AdvancedOptions(
            id_generator=IncrementalIdGenerator(),
            ns_timestamp_generator=time_generator,
        ),
        additional_span_processors=[SimpleSpanProcessor(exporter)],
    )
    return exporter


@pytest.fixture(autouse=True)
def _instrument_stack(exporter: TestExporter) -> None:
    instrument_agentseek_observability(force=True)


@pytest.fixture(autouse=True)
def _reset_bub_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.chdir(tmp_path)
    for key in ("BUB_MODEL", "BUB_API_FORMAT", "FAKE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    config_path = tmp_path / "empty-config.yml"
    _load_bub_config(config_path)
    yield
    _load_bub_config(config_path)


def test_any_llm_stream_span_waits_for_stream_consumption(
    exporter: TestExporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider(
        iter([
            {
                "kind": "stream",
                "chunks": [
                    {"choices": [{"delta": {"content": "hello "}}]},
                    {"choices": [{"delta": {"content": "world"}}]},
                    {"choices": [{"delta": {}, "finish_reason": "stop"}], "usage": {"total_tokens": 2}},
                ],
            }
        ])
    )
    monkeypatch.setattr(
        AnyLLM,
        "_create_provider",
        classmethod(lambda cls, provider_key, api_key=None, api_base=None, **kwargs: provider),
    )

    client = AnyLLM.create("fake")
    stream = asyncio.run(
        client.acompletion(
            model="demo-model",
            messages=[{"role": "user", "content": "say hello"}],
            stream=True,
        )
    )

    before_names = [span["name"] for span in exporter.exported_spans_as_dict(include_instrumentation_scope=True)]
    assert before_names == ["any_llm.create"]

    async def _collect() -> str:
        parts: list[str] = []
        async for chunk in stream:
            chunk_data = cast("dict[str, Any]", chunk)
            delta = cast("dict[str, Any]", chunk_data["choices"][0]["delta"]).get("content", "")
            if delta:
                parts.append(delta)
        return "".join(parts)

    assert asyncio.run(_collect()) == "hello world"

    spans = exporter.exported_spans_as_dict(include_instrumentation_scope=True, parse_json_attributes=True)
    names = [span["name"] for span in spans]
    assert names == ["any_llm.create", "any_llm.completion"]
    assert spans[-1]["instrumentation_scope"] == "logfire.any_llm"


def test_bub_republic_any_llm_stack_emits_nested_spans(
    exporter: TestExporter,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = FakeProvider(
        iter([
            {
                "kind": "response",
                "response": {
                    "choices": [
                        {
                            "message": {
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {"name": "help", "arguments": "{}"},
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
                },
            },
            {
                "kind": "response",
                "response": {
                    "choices": [{"message": {"content": "finished"}}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
                },
            },
        ])
    )
    monkeypatch.setenv("BUB_MODEL", "fake:demo-model")
    monkeypatch.setenv("BUB_API_FORMAT", "completion")
    monkeypatch.setattr(
        AnyLLM,
        "_create_provider",
        classmethod(lambda cls, provider_key, api_key=None, api_base=None, **kwargs: provider),
    )

    framework = BubFramework(config_file=tmp_path / "config.yml")
    framework._load_builtin_hooks()

    result = asyncio.run(
        framework.process_inbound({
            "content": "finish after calling help once",
            "channel": "cli",
            "chat_id": "chat-1",
        })
    )

    assert result.model_output == "finished"

    spans = exporter.exported_spans_as_dict(include_instrumentation_scope=True, parse_json_attributes=True)
    by_id = {span["context"]["span_id"]: span for span in spans}
    names = [span["name"] for span in spans]
    counts = Counter(names)
    scopes = {span["instrumentation_scope"] for span in spans}

    assert {"logfire.any_llm", "logfire.republic", "logfire.bub"} <= scopes
    assert counts["bub.process_inbound"] == 1
    assert counts["bub.agent.run"] == 1
    assert counts["bub.agent.step"] == 2
    assert counts["republic.run_chat"] == 2
    assert counts["republic.execute_tools"] == 1
    assert counts["republic.tool_call"] == 1
    assert counts["republic.record_chat"] == 2
    assert counts["any_llm.create"] == 1
    assert counts["any_llm.completion"] == 2

    def parent_name(span: dict[str, Any]) -> str | None:
        parent = span["parent"]
        if parent is None:
            return None
        return by_id[parent["span_id"]]["name"]

    assert parent_name(next(span for span in spans if span["name"] == "bub.agent.run")) == "bub.process_inbound"
    assert all(parent_name(span) == "bub.agent.run" for span in spans if span["name"] == "bub.agent.step")
    assert all(parent_name(span) == "bub.agent.step" for span in spans if span["name"] == "republic.run_chat")
    assert all(parent_name(span) == "republic.run_chat" for span in spans if span["name"] == "any_llm.completion")
    assert parent_name(next(span for span in spans if span["name"] == "republic.execute_tools")) == "republic.run_chat"
    assert parent_name(next(span for span in spans if span["name"] == "republic.tool_call")) == "republic.execute_tools"
