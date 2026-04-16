from __future__ import annotations

import asyncio
import importlib
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from bubseek_langchain.plugin import LangchainPlugin

pytest.importorskip("langgraph")


class _Framework:
    def get_system_prompt(self, prompt: str | list[dict[str, Any]], state: dict[str, Any]) -> str:
        return "system prompt"


def _write_module(tmp_path: Path, module_name: str, source: str) -> None:
    (tmp_path / f"{module_name}.py").write_text(textwrap.dedent(source), encoding="utf-8")
    sys.modules.pop(module_name, None)
    importlib.invalidate_caches()


def test_run_model_with_langgraph_factory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("BUB_LANGCHAIN_MODE", "runnable")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "lc_langgraph_factory:factory")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")

    _write_module(
        tmp_path,
        "lc_langgraph_factory",
        """
        from langchain_core.runnables import RunnableLambda
        from langgraph.graph import START, StateGraph
        from typing_extensions import TypedDict

        from bubseek_langchain.bridge import extract_prompt_text


        class GraphState(TypedDict):
            text: str
            answer: str


        def run_node(state: GraphState) -> dict[str, str]:
            return {"answer": f"LG:{state['text']}"}


        def factory(*, prompt, **kwargs):
            graph = StateGraph(GraphState)
            graph.add_node("run", run_node)
            graph.add_edge(START, "run")
            runnable = graph.compile() | RunnableLambda(lambda state: state["answer"])
            return runnable, {"text": extract_prompt_text(prompt)}
        """,
    )

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello langgraph", session_id="session-langgraph", state={}))

    assert result == "LG:hello langgraph"
