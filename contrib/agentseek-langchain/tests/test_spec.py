from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from agentseek_langchain.loader import load_spec_from_path, resolve_spec
from agentseek_langchain.profiles import messages_spec, text_spec
from agentseek_langchain.spec import InvocationContext
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


class _MessagesRunnable:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    async def ainvoke(self, runnable_input: object, config=None) -> dict[str, object]:
        self.calls.append((runnable_input, config))
        return {"messages": [AIMessage(content="agent-output")]}


def test_messages_spec_builds_message_state_and_extracts_output(tmp_path: Path) -> None:
    runnable = _MessagesRunnable()
    spec = messages_spec(runnable, include_agents_md=True)
    context = InvocationContext(
        prompt="hello",
        session_id="session-1",
        state={},
        workspace=tmp_path,
        agents_md="project-rules",
    )

    result = asyncio.run(spec.invoke(context))

    assert result == "agent-output"
    runnable_input, config = runnable.calls[0]
    assert config["configurable"]["thread_id"] == "session-1"
    assert runnable_input == {
        "messages": [
            SystemMessage(content="project-rules"),
            HumanMessage(content="hello"),
        ]
    }


def test_messages_spec_uses_ag_ui_messages_and_application_state(tmp_path: Path) -> None:
    runnable = _MessagesRunnable()
    spec = messages_spec(runnable, include_agents_md=True)
    context = InvocationContext(
        prompt="ignored",
        session_id="session-1",
        state={
            "customer_id": "cust-7",
            "_ag_ui": {
                "messages": [
                    {"id": "user-1", "role": "user", "content": "hello"},
                    {
                        "id": "assistant-1",
                        "role": "assistant",
                        "content": "I can help",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {"name": "lookup", "arguments": '{"city":"Shanghai"}'},
                            }
                        ],
                    },
                    {"id": "tool-1", "role": "tool", "tool_call_id": "call-1", "content": '{"weather":"sunny"}'},
                ],
                "tools": [{"name": "lookup", "description": "Lookup data", "parameters": {"type": "object"}}],
                "context": [{"description": "tenant", "value": "demo"}],
            },
        },
        workspace=tmp_path,
        agents_md="project-rules",
    )

    result = asyncio.run(spec.invoke(context))

    assert result == "agent-output"
    runnable_input, _config = runnable.calls[0]
    assert runnable_input["customer_id"] == "cust-7"
    assert runnable_input["tools"] == [
        {"name": "lookup", "description": "Lookup data", "parameters": {"type": "object"}}
    ]
    assert runnable_input["copilotkit"] == {
        "actions": [{"name": "lookup", "description": "Lookup data", "parameters": {"type": "object"}}],
        "context": [{"description": "tenant", "value": "demo"}],
    }
    assert runnable_input["messages"] == [
        SystemMessage(content="project-rules"),
        HumanMessage(id="user-1", content="hello", name=None),
        AIMessage(
            id="assistant-1",
            content="I can help",
            name=None,
            tool_calls=[{"id": "call-1", "name": "lookup", "args": {"city": "Shanghai"}, "type": "tool_call"}],
        ),
        ToolMessage(id="tool-1", tool_call_id="call-1", content='{"weather":"sunny"}'),
    ]


def test_text_spec_rejects_multimodal_prompt(tmp_path: Path) -> None:
    spec = text_spec(object())
    context = InvocationContext(
        prompt=[{"type": "text", "text": "hello"}],
        session_id="session-1",
        state={},
        workspace=tmp_path,
        agents_md=None,
    )

    with pytest.raises(TypeError, match="text_spec only supports string prompts"):
        spec.build_input(context)


def test_resolve_spec_accepts_zero_argument_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = tmp_path / "binding_module.py"
    module_path.write_text(
        "\n".join([
            "from agentseek_langchain import text_spec",
            "",
            "class Runnable:",
            "    async def ainvoke(self, input, config=None):",
            "        return 'ok'",
            "",
            "def build_spec():",
            "    return text_spec(Runnable())",
        ])
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    spec = load_spec_from_path("binding_module:build_spec")

    assert spec.parse_output("ok") == "ok"


def test_resolve_spec_rejects_bare_runnable() -> None:
    class Runnable:
        async def ainvoke(self, runnable_input, config=None):
            del runnable_input, config
            return "ok"

    with pytest.raises(TypeError, match="RunnableSpec"):
        resolve_spec(Runnable())
