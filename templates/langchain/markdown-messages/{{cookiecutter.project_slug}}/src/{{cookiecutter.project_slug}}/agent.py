"""LangChain `create_agent` graph, served by `langgraph dev`.

This module is pure LangChain - no agentseek dependency. The 4-line
``AGENTSEEK_*`` to ``OPENAI_*`` bridge is a convenience for users whose
``.env`` only carries agentseek-style credentials.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

load_dotenv()

if os.getenv("AGENTSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AGENTSEEK_API_KEY"]
if os.getenv("AGENTSEEK_API_BASE") and not os.getenv("OPENAI_API_BASE"):
    os.environ["OPENAI_API_BASE"] = os.environ["AGENTSEEK_API_BASE"]

model_name = (
    os.getenv("AGENTSEEK_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "{{ cookiecutter.default_model }}"
)
model = init_chat_model(model_name)

graph = create_agent(
    model=model,
    tools=[],
    system_prompt="""{{ cookiecutter.system_prompt }}""",
)
