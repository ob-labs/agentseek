from __future__ import annotations

import asyncio
from types import SimpleNamespace

import agentseek_langchain.plugin as plugin_module
from agentseek_langchain.profiles import text_spec


class _AsyncRunnable:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[object, object]] = []

    async def ainvoke(self, runnable_input: object, config=None) -> str:
        self.calls.append((runnable_input, config))
        return self.output


def test_plugin_run_model_delegates_to_loaded_spec(monkeypatch, tmp_path) -> None:
    runnable = _AsyncRunnable("delegated-output")
    spec = text_spec(runnable)

    monkeypatch.setattr(plugin_module, "get_langchain_settings", lambda: SimpleNamespace(spec="dummy:SPEC"))
    monkeypatch.setattr(plugin_module, "load_spec_from_path", lambda path: spec)

    plugin = plugin_module.LangChainRunnablePlugin()
    result = asyncio.run(
        plugin.run_model(
            prompt="hello",
            session_id="session-1",
            state={"_runtime_workspace": str(tmp_path)},
        )
    )

    assert result == "delegated-output"
    assert runnable.calls[0][0] == "hello"
    assert runnable.calls[0][1]["metadata"]["session_id"] == "session-1"


def test_plugin_run_model_stream_wraps_single_result(monkeypatch, tmp_path) -> None:
    runnable = _AsyncRunnable("streamed-once")
    spec = text_spec(runnable)

    monkeypatch.setattr(plugin_module, "get_langchain_settings", lambda: SimpleNamespace(spec="dummy:SPEC"))
    monkeypatch.setattr(plugin_module, "load_spec_from_path", lambda path: spec)

    plugin = plugin_module.LangChainRunnablePlugin()
    stream = asyncio.run(
        plugin.run_model_stream(
            prompt="hello",
            session_id="session-1",
            state={"_runtime_workspace": str(tmp_path)},
        )
    )
    events = asyncio.run(_collect_events(stream))

    assert [(event.kind, event.data) for event in events] == [
        ("text", {"delta": "streamed-once"}),
        ("final", {"text": "streamed-once", "ok": True}),
    ]


async def _collect_events(stream) -> list:
    return [event async for event in stream]
