"""DeepAgents research graph, served by `langgraph dev`.

This module is pure deepagents + LangChain — no agentseek dependency. It
mirrors the upstream ``langchain-ai/deepagents/examples/deep_research/agent.py``
with these differences:
- ``init_chat_model`` is called with the ``openai:`` prefix so the template
  works against any OpenAI-compatible endpoint by default.
- The ``AGENTSEEK_*`` → ``OPENAI_*`` env bridge is included near the top so
  the same ``.env`` that works for ``langchain/markdown-messages`` works
  here too.
- The orchestrator and sub-agent constants are wired to cookiecutter
  variables so they can be tuned at scaffold time.
"""

from __future__ import annotations

import os
import warnings
from datetime import datetime

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from {{ cookiecutter.project_slug }}.prompts import (
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from {{ cookiecutter.project_slug }}.tools import tavily_search, think_tool

load_dotenv()

if os.getenv("AGENTSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AGENTSEEK_API_KEY"]
if os.getenv("AGENTSEEK_API_BASE") and not os.getenv("OPENAI_API_BASE"):
    os.environ["OPENAI_API_BASE"] = os.environ["AGENTSEEK_API_BASE"]

# Some OpenAI-compatible gateways can pause for longer than LangChain OpenAI's
# default 120s chunk gap while streaming a large tool-call payload.
_stream_chunk_timeout_env = os.getenv("LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S")
STREAM_CHUNK_TIMEOUT_S: float | None = 300.0
if _stream_chunk_timeout_env not in (None, ""):
    try:
        _parsed_timeout = float(_stream_chunk_timeout_env)
    except ValueError:
        warnings.warn(
            "Ignoring invalid LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S value; "
            "using the default 300s timeout instead.",
            stacklevel=2,
        )
    else:
        STREAM_CHUNK_TIMEOUT_S = None if _parsed_timeout <= 0 else _parsed_timeout

MAX_CONCURRENT_RESEARCH_UNITS = {{ cookiecutter.max_concurrent_research_units }}
MAX_RESEARCHER_ITERATIONS = {{ cookiecutter.max_researcher_iterations }}

current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=MAX_CONCURRENT_RESEARCH_UNITS,
        max_researcher_iterations=MAX_RESEARCHER_ITERATIONS,
    )
)

research_sub_agent = {
    "name": "research-agent",
    "description": (
        "Delegate research to the sub-agent researcher. "
        "Only give this researcher one topic at a time."
    ),
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool],
}

model = init_chat_model(
    "{{ cookiecutter.default_model }}",
    stream_chunk_timeout=STREAM_CHUNK_TIMEOUT_S,
)

graph = create_deep_agent(
    model=model,
    tools=[tavily_search, think_tool],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)
