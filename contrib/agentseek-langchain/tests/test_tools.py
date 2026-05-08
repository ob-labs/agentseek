import asyncio

import pytest
from agentseek_langchain.errors import LangchainConfigError
from agentseek_langchain.tools import bub_tool_to_langchain
from bub.tools import tool as bub_tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel
from republic import Tool, ToolContext


class Filters(BaseModel):
    mode: str
    tags: list[str]


class MessageMedia(BaseModel):
    media_type: str
    file_path: str


class MessagePayload(BaseModel):
    text: str
    media: MessageMedia | None = None


@bub_tool(name="search-docs")
def search_docs(query: str, filters: Filters) -> dict[str, object]:
    """Search docs."""

    return {
        "query": query,
        "filters": filters.model_dump(),
    }


@bub_tool(name="sample.tool", context=True)
def sample_tool(value: str, *, context: ToolContext) -> str:
    """Sample tool."""

    return f"{context.run_id}:{value}"


@bub_tool(name="wechat")
def send_wechat(message: MessagePayload) -> dict[str, object]:
    """Send a WeChat message."""

    return message.model_dump()


@bub_tool(name="async.tool", context=True)
async def async_tool(value: str, *, context: ToolContext) -> str:
    """Async tool."""

    return f"{context.run_id}:{value}"


def test_bub_tool_to_langchain_uses_bub_function_schema() -> None:
    langchain_tool = bub_tool_to_langchain(
        search_docs,
        tool_context=ToolContext(tape=None, run_id="run-1", state={}),
    )

    openai_tool = convert_to_openai_tool(langchain_tool)
    filters_schema = openai_tool["function"]["parameters"]["properties"]["filters"]

    assert langchain_tool.name == "search-docs"
    assert filters_schema["properties"]["mode"]["type"] == "string"
    assert filters_schema["properties"]["tags"]["items"] == {"type": "string"}


def test_bub_tool_to_langchain_passes_context_to_handler() -> None:
    tool_context = ToolContext(tape="tape-x", run_id="run-1", state={"x": 1})

    langchain_tool = bub_tool_to_langchain(sample_tool, tool_context=tool_context)
    result = langchain_tool.invoke({"value": "hi"})

    assert langchain_tool.name == "sample.tool"
    assert result == "run-1:hi"


def test_bub_tool_to_langchain_supports_nested_pydantic_models() -> None:
    langchain_tool = bub_tool_to_langchain(
        send_wechat,
        tool_context=ToolContext(tape=None, run_id="run-1", state={}),
    )
    openai_tool = convert_to_openai_tool(langchain_tool)

    media_schema = openai_tool["function"]["parameters"]["properties"]["message"]["properties"]["media"]["anyOf"][0]
    assert media_schema["properties"]["media_type"]["type"] == "string"
    assert media_schema["properties"]["file_path"]["type"] == "string"


def test_bub_tool_to_langchain_supports_async_handlers() -> None:
    tool_context = ToolContext(tape=None, run_id="run-async", state={})
    langchain_tool = bub_tool_to_langchain(async_tool, tool_context=tool_context)

    assert asyncio.run(langchain_tool.ainvoke({"value": "hi"})) == "run-async:hi"


def test_bub_tool_to_langchain_rejects_schema_only_tool() -> None:
    bub_tool_instance = Tool(
        name="schema.only",
        description="Schema only",
        parameters={},
        handler=None,
    )

    with pytest.raises(LangchainConfigError, match="schema-only"):
        bub_tool_to_langchain(
            bub_tool_instance,
            tool_context=ToolContext(tape=None, run_id="run-1", state={}),
        )
