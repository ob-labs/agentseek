"""Content builder tools: web search and image generation.

Provides ``web_search`` (Tavily-backed web discovery), ``generate_cover``
(blog hero image via Gemini), and ``generate_social_image`` (social post
image via Gemini). These are wired into the deep agent and its subagents
at startup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from langchain_core.tools import InjectedToolArg, tool
from typing_extensions import Annotated

EXAMPLE_DIR = Path(__file__).resolve().parents[2]

GOOGLE_IMAGE_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", "{{ cookiecutter.google_image_model }}")


def _safe_path(base: Path, *segments: str) -> Path | None:
    """Join path segments and verify the result stays under base."""
    output = (base / Path(*segments)).resolve()
    if not output.is_relative_to(base.resolve()):
        return None
    return output


def _generate_image(prompt: str, output_path: Path) -> str:
    """Generate an image with Gemini and save to disk."""
    try:
        from google import genai

        api_key = os.getenv("GOOGLE_API_KEY", "").strip() or None
        if not api_key:
            return "Error: GOOGLE_API_KEY not set"

        client_kwargs: dict = {"api_key": api_key}
        api_base = os.getenv("GOOGLE_API_BASE", "").strip() or None
        if api_base:
            client_kwargs["http_options"] = {"base_url": api_base}

        client = genai.Client(**client_kwargs)
        response = client.models.generate_content(
            model=GOOGLE_IMAGE_MODEL,
            contents=[prompt],
            config={"response_modalities": ["IMAGE"]},
        )

        for part in (response.parts or []):
            if part.inline_data is not None:
                image = part.as_image()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(str(output_path))
                return f"Image saved to {output_path.relative_to(EXAMPLE_DIR)}"

        return "No image generated — model returned no image data"
    except Exception as e:
        return f"Error generating image: {e}"


@tool(parse_docstring=True)
def web_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = {{ cookiecutter.tavily_max_results }},
    topic: Annotated[
        Literal["general", "news"], InjectedToolArg
    ] = "{{ cookiecutter.tavily_topic }}",
) -> dict:
    """Search the web for current information on a given query.

    Args:
        query: The search query — be specific and detailed.
        max_results: Maximum number of results to return.
        topic: Topic filter — 'general' for most queries, 'news' for current events.

    Returns:
        Search results with titles, URLs, and content excerpts.
    """
    try:
        from tavily import TavilyClient

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return {"error": "TAVILY_API_KEY not set"}

        client = TavilyClient(api_key=api_key)
        return client.search(query, max_results=max_results, topic=topic)
    except Exception as e:
        return {"error": f"Search failed: {e}"}


@tool(parse_docstring=True)
def generate_cover(prompt: str, slug: str) -> str:
    """Generate a cover image for a blog post.

    Args:
        prompt: Detailed description of the image to generate.
        slug: Blog post slug. Image saves to blogs/<slug>/hero.png.
    """
    output_path = _safe_path(EXAMPLE_DIR, "blogs", slug, "hero.png")
    if output_path is None:
        return "Error: invalid slug (path traversal)"
    return _generate_image(prompt, output_path)


ALLOWED_PLATFORMS = {"linkedin", "tweets"}


@tool(parse_docstring=True)
def generate_social_image(prompt: str, platform: str, slug: str) -> str:
    """Generate an image for a social media post.

    Args:
        prompt: Detailed description of the image to generate.
        platform: Either "linkedin" or "tweets".
        slug: Post slug. Image saves to <platform>/<slug>/image.png.
    """
    if platform not in ALLOWED_PLATFORMS:
        return f"Error: platform must be one of {sorted(ALLOWED_PLATFORMS)}"
    output_path = _safe_path(EXAMPLE_DIR, platform, slug, "image.png")
    if output_path is None:
        return "Error: invalid slug (path traversal)"
    return _generate_image(prompt, output_path)
