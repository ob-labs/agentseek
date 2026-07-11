"""Dataset-scoped RAGFlow tools with approval gates for mutations."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.tools import tool
from langgraph.types import interrupt

from {{ cookiecutter.project_slug }}.ragflow import RAGFlowAdapter


@lru_cache(maxsize=1)
def _adapter() -> RAGFlowAdapter:
    return RAGFlowAdapter.from_env()


def _approved(payload: dict[str, Any]) -> bool:
    response = interrupt(payload)
    return isinstance(response, dict) and response.get("approved") is True


@tool
def list_ragflow_datasets(
    page: int = 1,
    page_size: int = 30,
) -> list[dict[str, Any]]:
    """List one bounded page of RAGFlow datasets available to the API key."""
    return _adapter().list_datasets(page=page, page_size=page_size)


@tool
def retrieve_ragflow(
    question: str,
    dataset_ids: list[str],
    max_chunks: int = 8,
) -> list[dict[str, Any]]:
    """Retrieve evidence from explicit RAGFlow dataset IDs."""
    return _adapter().retrieve(
        question=question,
        dataset_ids=dataset_ids,
        max_chunks=max_chunks,
    )


@tool
def upload_staged_documents(
    dataset_id: str,
    relative_paths: list[str],
) -> list[dict[str, Any]] | dict[str, Any]:
    """Request approval, then upload staged server-local files to one dataset."""
    if not relative_paths:
        raise ValueError("relative_paths must contain at least one staged file")
    operation = {
        "kind": "ragflow_approval",
        "operation": "upload_documents",
        "dataset_id": dataset_id,
        "relative_paths": relative_paths,
        "count": len(relative_paths),
    }
    if not _approved(operation):
        return {
            "status": "cancelled",
            "operation": "upload_documents",
            "dataset_id": dataset_id,
        }
    return _adapter().upload_documents(
        dataset_id=dataset_id,
        relative_paths=relative_paths,
    )


@tool
def parse_ragflow_documents(
    dataset_id: str,
    document_ids: list[str],
) -> dict[str, Any]:
    """Request approval, then start asynchronous parsing for documents."""
    if not document_ids:
        raise ValueError("document_ids must contain at least one document ID")
    operation = {
        "kind": "ragflow_approval",
        "operation": "parse_documents",
        "dataset_id": dataset_id,
        "document_ids": document_ids,
        "count": len(document_ids),
    }
    if not _approved(operation):
        return {
            "status": "cancelled",
            "operation": "parse_documents",
            "dataset_id": dataset_id,
        }
    return _adapter().parse_documents(
        dataset_id=dataset_id,
        document_ids=document_ids,
    )
