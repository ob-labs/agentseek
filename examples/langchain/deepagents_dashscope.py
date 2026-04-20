from __future__ import annotations

import importlib
import os
from typing import Any

DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_DEEPAGENTS_MODEL = "glm-5.1"


class DashScopeExampleError(RuntimeError):
    """Base error for the DashScope deepagents example."""


class MissingDashScopeEnvError(DashScopeExampleError):
    """Raised when a required DashScope environment variable is missing."""

    def __init__(self, name: str) -> None:
        super().__init__(f"{name} is required for the DashScope deepagents example")


class MissingLangChainOpenAIError(DashScopeExampleError):
    """Raised when langchain-openai is not installed."""

    def __init__(self) -> None:
        super().__init__(
            "langchain-openai is required for the DashScope deepagents example. Install the langchain extra first."
        )


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def _require_env(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value and value.strip():
        return value.strip()
    raise MissingDashScopeEnvError(name)


def _build_chat_model() -> Any:
    try:
        module = importlib.import_module("langchain_openai")
    except ModuleNotFoundError as exc:
        raise MissingLangChainOpenAIError from exc

    chat_openai_cls = module.ChatOpenAI

    return chat_openai_cls(
        model=os.getenv("BUB_MODEL", DEFAULT_DEEPAGENTS_MODEL),
        api_key=_require_env("BUB_API_KEY"),
        base_url=os.getenv("BUB_API_BASE", DEFAULT_DASHSCOPE_BASE_URL),
        temperature=0,
    )


def _extract_prompt_text(prompt: str | list[dict[str, Any]]) -> str:
    if isinstance(prompt, str):
        return prompt

    texts: list[str] = []
    for part in prompt:
        if not isinstance(part, dict):
            continue
        if part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text)
    return "\n".join(texts).strip()


def dashscope_deep_agent(
    *,
    tools: list[Any] | None = None,
    system_prompt: str = "",
    prompt: str | list[dict[str, Any]],
    **_: Any,
) -> tuple[Any, dict[str, list[dict[str, str]]]]:
    """Build a DeepAgents runnable backed by DashScope's OpenAI-compatible API."""

    from deepagents import create_deep_agent
    from langchain_core.runnables import RunnableLambda

    prompt_text = _extract_prompt_text(prompt)
    agent = create_deep_agent(
        model=_build_chat_model(),
        tools=[get_weather, *(tools or [])],
        system_prompt=system_prompt or "You are a helpful assistant",
    )
    runnable = agent | RunnableLambda(lambda state: state["messages"][-1].content)
    invoke_input = {"messages": [{"role": "user", "content": prompt_text}]}
    return runnable, invoke_input
