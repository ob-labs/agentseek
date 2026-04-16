from __future__ import annotations

from bubseek_langchain.tools import bub_tool_to_langchain
from republic import Tool, ToolContext


def test_bub_tool_to_langchain_preserves_nested_json_schema() -> None:
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 1,
            },
            "filters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["and", "or"],
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["mode", "tags"],
                "additionalProperties": False,
            },
        },
        "required": ["query", "filters"],
        "additionalProperties": False,
    }
    bub_tool = Tool(
        name="search-docs",
        description="Search docs",
        parameters=parameters,
        handler=lambda **kwargs: kwargs,
    )

    langchain_tool = bub_tool_to_langchain(
        bub_tool,
        tool_context=ToolContext(tape=None, run_id="run-1", state={}),
    )

    assert isinstance(langchain_tool.args_schema, dict)
    assert langchain_tool.args_schema == parameters
    assert langchain_tool.tool_call_schema["properties"]["filters"]["properties"]["mode"]["enum"] == ["and", "or"]
    assert langchain_tool.tool_call_schema["properties"]["filters"]["properties"]["tags"]["items"] == {
        "type": "string"
    }
