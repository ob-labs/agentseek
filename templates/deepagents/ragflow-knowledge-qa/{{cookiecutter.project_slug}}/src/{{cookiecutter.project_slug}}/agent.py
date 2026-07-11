"""DeepAgents graph for RAGFlow-backed knowledge-base Q&A."""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from {{ cookiecutter.project_slug }}.prompts import SYSTEM_PROMPT
from {{ cookiecutter.project_slug }}.tools import (
    list_ragflow_datasets,
    parse_ragflow_documents,
    retrieve_ragflow,
    upload_staged_documents,
)

load_dotenv()


def _required_env(name: str, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


model = ChatOpenAI(
    model=_required_env("AGENTSEEK_MODEL", "{{ cookiecutter.default_model }}"),
    api_key=_required_env("AGENTSEEK_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    base_url=os.getenv("AGENTSEEK_API_BASE") or os.getenv("OPENAI_API_BASE") or None,
)

knowledge_sub_agent = {
    "name": "knowledge-researcher",
    "description": "Retrieve evidence from one or more explicit RAGFlow dataset IDs.",
    "system_prompt": (
        SYSTEM_PROMPT
        + "\nYou are read-only. Never request uploads or parsing. Return evidence and scope."
    ),
    "tools": [list_ragflow_datasets, retrieve_ragflow],
}

graph = create_deep_agent(
    model=model,
    tools=[
        list_ragflow_datasets,
        retrieve_ragflow,
        upload_staged_documents,
        parse_ragflow_documents,
    ],
    system_prompt=SYSTEM_PROMPT,
    subagents=[knowledge_sub_agent],
)
