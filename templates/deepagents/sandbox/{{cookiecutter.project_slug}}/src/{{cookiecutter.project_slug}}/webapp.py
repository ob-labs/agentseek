"""Custom LangGraph server app with graceful sandbox cleanup."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from {{ cookiecutter.project_slug }}.agent import cleanup_sandbox


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        cleanup_sandbox()


app = FastAPI(lifespan=lifespan)
