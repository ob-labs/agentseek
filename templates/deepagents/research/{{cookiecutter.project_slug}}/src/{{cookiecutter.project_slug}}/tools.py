"""Research tools for the deepagent.

Provides ``tavily_search`` (web discovery + full-page fetch as markdown)
and ``think_tool`` (no-op reflection sink used to slow the agent down
after each search). Mirrors the upstream
``langchain-ai/deepagents/examples/deep_research/research_agent/tools.py``
verbatim apart from the default ``max_results`` / ``topic`` values, which
are wired to cookiecutter variables so the user can tune at scaffold time.
"""

from __future__ import annotations

import httpx
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

tavily_client = TavilyClient()


def fetch_webpage_content(url: str, timeout: float = 15.0) -> str:
    """Fetch and convert webpage content to markdown.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Webpage content as markdown, or an error string on failure.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
        return markdownify(response.text)
    except Exception as exc:
        return f"Error fetching content from {url}: {exc!s}"


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = {{ cookiecutter.tavily_max_results }},
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "{{ cookiecutter.tavily_topic }}",
) -> str:
    """Search the web for information on a given query.

    Uses Tavily to discover relevant URLs, then fetches and returns full
    webpage content as markdown.

    Args:
        query: Search query to execute.
        max_results: Maximum number of results to return.
        topic: Topic filter — 'general', 'news', or 'finance'.

    Returns:
        Formatted search results with full webpage content.
    """
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    result_texts: list[str] = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]
        content = fetch_webpage_content(url)
        result_texts.append(
            f"## {title}\n"
            f"**URL:** {url}\n\n"
            f"{content}\n\n"
            "---\n"
        )

    return (
        f"🔍 Found {len(result_texts)} result(s) for '{query}':\n\n"
        + "\n".join(result_texts)
    )


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps
    systematically. Creates a deliberate pause in the research workflow.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings — What concrete information have I gathered?
    2. Gap assessment — What crucial information is still missing?
    3. Quality evaluation — Do I have sufficient evidence for a good answer?
    4. Strategic decision — Should I continue searching or provide my answer?

    Args:
        reflection: Detailed reflection on research progress, findings, gaps,
            and next steps.

    Returns:
        Confirmation that reflection was recorded for decision-making.
    """
    return f"Reflection recorded: {reflection}"
