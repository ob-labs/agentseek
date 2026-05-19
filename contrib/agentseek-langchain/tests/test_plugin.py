from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace

import agentseek_langchain.plugin as plugin_module
import typer
from agentseek_langchain.profiles import text_spec
from agentseek_langchain.shapes import ObjectDict, copy_str_mapping
from typer.testing import CliRunner


class _AsyncRunnable:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[object, ObjectDict | None]] = []

    async def ainvoke(self, runnable_input: object, config: ObjectDict | None = None) -> str:
        self.calls.append((runnable_input, config))
        return self.output


class _AsyncRunnableWithContext:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[object, ObjectDict | None, ObjectDict | None]] = []

    async def ainvoke(
        self,
        runnable_input: object,
        config: ObjectDict | None = None,
        context: ObjectDict | None = None,
    ) -> str:
        self.calls.append((runnable_input, config, context))
        return self.output


class _FakeAgentSeekApiCliModule:
    def __init__(self, exit_code: int, captured: dict[str, object]) -> None:
        self._exit_code = exit_code
        self._captured = captured

    def main(
        self,
        argv: Sequence[str] | None = None,
        *,
        prog: str | None = None,
        cwd: str | Path | None = None,
    ) -> int:
        self._captured["argv"] = list(argv or [])
        self._captured["prog"] = prog
        self._captured["cwd"] = cwd
        return self._exit_code


def test_plugin_run_model_delegates_to_loaded_spec(monkeypatch, tmp_path) -> None:
    runnable = _AsyncRunnable("delegated-output")
    spec = text_spec(runnable)

    monkeypatch.setattr(plugin_module, "get_langchain_settings", lambda: SimpleNamespace(SPEC="dummy:SPEC"))
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
    metadata = copy_str_mapping(runnable.calls[0][1].get("metadata") if runnable.calls[0][1] else None)
    assert metadata == {
        "session_id": "session-1",
        "workspace": str(tmp_path),
    }


def test_plugin_run_model_stream_wraps_single_result(monkeypatch, tmp_path) -> None:
    runnable = _AsyncRunnable("streamed-once")
    spec = text_spec(runnable)

    monkeypatch.setattr(plugin_module, "get_langchain_settings", lambda: SimpleNamespace(SPEC="dummy:SPEC"))
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


def test_plugin_passes_ag_ui_context_as_runtime_context(monkeypatch, tmp_path) -> None:
    runnable = _AsyncRunnableWithContext("delegated-output")
    spec = text_spec(runnable)

    monkeypatch.setattr(plugin_module, "get_langchain_settings", lambda: SimpleNamespace(SPEC="dummy:SPEC"))
    monkeypatch.setattr(plugin_module, "load_spec_from_path", lambda path: spec)

    plugin = plugin_module.LangChainRunnablePlugin()
    result = asyncio.run(
        plugin.run_model(
            prompt="hello",
            session_id="session-1",
            state={
                "_runtime_workspace": str(tmp_path),
                "_ag_ui": {
                    "context": [
                        {"description": "tenant", "value": "demo"},
                        {
                            "description": "output_schema",
                            "value": '{"type":"object","properties":{"name":{"type":"string"}}}',
                        },
                    ]
                },
            },
        )
    )

    assert result == "delegated-output"
    assert runnable.calls[0][2] == {
        "tenant": "demo",
        "output_schema": {"type": "object", "properties": {"name": {"type": "string"}}},
    }


async def _collect_events(stream) -> list:
    return [event async for event in stream]


def test_plugin_registers_api_cli_group_once() -> None:
    app = typer.Typer()
    plugin = plugin_module.LangChainRunnablePlugin()

    plugin.register_cli_commands(app)
    plugin.register_cli_commands(app)

    groups = [group.name for group in app.registered_groups]
    assert groups.count("api") == 1

    result = CliRunner().invoke(app, ["api", "--help"])

    assert result.exit_code == 0
    assert "dev" in result.stdout
    assert "serve" in result.stdout
    assert "dockerfile" in result.stdout
    assert "build" in result.stdout
    assert "up" in result.stdout
    assert "version" in result.stdout


def test_api_cli_forwards_arguments_to_agentseek_api(monkeypatch) -> None:
    import agentseek_langchain.api_cli as api_cli_module

    captured: dict[str, object] = {}
    fake_module = _FakeAgentSeekApiCliModule(exit_code=7, captured=captured)

    monkeypatch.setattr(api_cli_module.importlib, "import_module", lambda name: fake_module)

    app = typer.Typer()
    plugin_module.LangChainRunnablePlugin().register_cli_commands(app)
    result = CliRunner().invoke(app, ["api", "dev", "--port", "9911", "--no-reload"])

    assert result.exit_code == 7
    assert captured["argv"] == ["dev", "--port", "9911", "--no-reload"]
    assert captured["prog"] == "agentseek api"
    assert captured["cwd"] == Path.cwd().resolve()


def test_api_cli_reports_missing_agentseek_api_dependency(monkeypatch) -> None:
    import agentseek_langchain.api_cli as api_cli_module

    def fail_import(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(api_cli_module.importlib, "import_module", fail_import)

    app = typer.Typer()
    plugin_module.LangChainRunnablePlugin().register_cli_commands(app)
    result = CliRunner().invoke(app, ["api", "version"])

    assert result.exit_code == 1
    assert "agentseek-api" in result.stderr
