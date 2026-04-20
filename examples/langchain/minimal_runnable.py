from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableLambda


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


def minimal_lc_agent(
    *,
    tools: list[Any] | None = None,
    system_prompt: str = "",
    prompt: str | list[dict[str, Any]],
    **_: Any,
) -> tuple[RunnableLambda, str]:
    """Return a minimal Runnable showing how Bub injects tools and prompt context."""

    tool_names = [getattr(tool, "name", "tool") for tool in tools or []]
    prompt_prefix = system_prompt.strip().splitlines()[0] if system_prompt.strip() else "No system prompt"

    def _run(text: str) -> str:
        summary = f"[minimal_lc_agent] {text.strip()}"
        if tool_names:
            return f"{summary}\nTools: {', '.join(tool_names)}\nSystem: {prompt_prefix}"
        return f"{summary}\nSystem: {prompt_prefix}"

    return RunnableLambda(_run), _extract_prompt_text(prompt)
