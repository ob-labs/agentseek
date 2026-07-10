"""RAGFlow SDK adapter."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


class RAGFlowAdapter:
    """Keep RAGFlow SDK objects behind a small, serializable interface."""

    def __init__(self, client: Any, upload_root: str | Path) -> None:
        self.client = client
        self.upload_root = Path(upload_root)

    @classmethod
    def from_env(cls) -> "RAGFlowAdapter":
        """Build the pinned SDK client from generated-app configuration."""
        from ragflow_sdk import RAGFlow

        base_url = os.getenv("RAGFLOW_BASE_URL", "").strip().rstrip("/")
        api_key = os.getenv("RAGFLOW_API_KEY", "").strip()
        if not base_url:
            raise ValueError("RAGFLOW_BASE_URL is required")
        if not api_key:
            raise ValueError("RAGFLOW_API_KEY is required")
        client = RAGFlow(api_key=api_key, base_url=base_url)
        return cls(
            client=client,
            upload_root=os.getenv("RAGFLOW_UPLOAD_ROOT", "./uploads"),
        )

    @staticmethod
    def _sdk_call(operation: str, call: Callable[[], T]) -> T:
        try:
            return call()
        except Exception:
            raise RuntimeError(f"RAGFlow {operation} failed") from None

    def list_datasets(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
    ) -> list[dict[str, Any]]:
        """Return compact metadata suitable for explicit scope selection."""
        if page < 1:
            raise ValueError("page must be at least 1")
        if not 1 <= page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")
        datasets = self._sdk_call(
            "dataset listing",
            lambda: self.client.list_datasets(page=page, page_size=page_size),
        )
        fields = ("id", "name", "description", "document_count", "chunk_count")
        return [{field: getattr(dataset, field, None) for field in fields} for dataset in datasets]

    def _resolve_upload_path(self, relative_path: str) -> Path:
        root = self.upload_root.resolve()
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("upload paths must stay within RAGFLOW_UPLOAD_ROOT") from exc
        if not candidate.is_file():
            raise ValueError(f"staged upload is not a file: {relative_path}")
        return candidate

    def _get_dataset(self, dataset_id: str) -> Any:
        datasets = self._sdk_call(
            "dataset lookup",
            lambda: self.client.list_datasets(id=dataset_id),
        )
        if len(datasets) != 1:
            raise ValueError(f"RAGFlow dataset not found: {dataset_id}")
        return datasets[0]

    def upload_documents(
        self,
        *,
        dataset_id: str,
        relative_paths: list[str],
    ) -> list[dict[str, Any]]:
        """Upload server-local files after resolving them below the staging root."""
        if not relative_paths:
            raise ValueError("relative_paths must contain at least one staged file")
        paths = [self._resolve_upload_path(relative_path) for relative_path in relative_paths]
        payload = [{"display_name": path.name, "blob": path.read_bytes()} for path in paths]
        dataset = self._get_dataset(dataset_id)
        documents = self._sdk_call(
            "document upload",
            lambda: dataset.upload_documents(payload),
        )
        return [
            {
                "id": getattr(document, "id", None),
                "name": getattr(document, "name", getattr(document, "display_name", None)),
            }
            for document in documents
        ]

    def parse_documents(
        self,
        *,
        dataset_id: str,
        document_ids: list[str],
    ) -> dict[str, Any]:
        """Start asynchronous parsing and return without polling."""
        if not document_ids:
            raise ValueError("document_ids must contain at least one document ID")
        dataset = self._get_dataset(dataset_id)
        self._sdk_call(
            "document parsing",
            lambda: dataset.async_parse_documents(document_ids),
        )
        return {
            "status": "accepted",
            "dataset_id": dataset_id,
            "document_ids": document_ids,
        }

    def retrieve(
        self,
        *,
        dataset_ids: list[str],
        question: str,
        max_chunks: int = 8,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks from an explicit dataset scope."""
        if not dataset_ids:
            raise ValueError("dataset_ids must contain at least one dataset ID")
        if not 1 <= max_chunks <= 20:
            raise ValueError("max_chunks must be between 1 and 20")
        chunks = self._sdk_call(
            "retrieval",
            lambda: self.client.retrieve(
                dataset_ids=dataset_ids,
                question=question,
                page=1,
                page_size=max_chunks,
                similarity_threshold=0.2,
                vector_similarity_weight=0.3,
                top_k=1024,
            ),
        )
        fields = (
            "id",
            "content",
            "dataset_id",
            "document_id",
            "document_name",
            "similarity",
        )
        return [{field: getattr(chunk, field, None) for field in fields} for chunk in chunks]
