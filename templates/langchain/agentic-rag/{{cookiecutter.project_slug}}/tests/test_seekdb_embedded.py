"""Network-free embedded seekdb proof."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from {{ cookiecutter.project_slug }}.vector_store import get_vector_store


pytest.importorskip("pylibseekdb", reason="embedded seekdb bindings are unavailable")


class DeterministicEmbeddings(Embeddings):
    @staticmethod
    def _vector(first: float, second: float) -> list[float]:
        return [first, second] + [0.0] * 382

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(1.0, 0.0) if "embedded" in text else self._vector(0.0, 1.0) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(1.0, 0.0) if "embedded" in text else self._vector(0.0, 1.0)


def _run_smoke(path: Path) -> None:
    os.environ["SEEKDB_PATH"] = str(path)
    store = get_vector_store(DeterministicEmbeddings())
    store.add_documents(
        [
            Document(page_content="embedded seekdb is local", metadata={"source": "embedded"}),
            Document(page_content="server seekdb is optional", metadata={"source": "server"}),
        ]
    )
    results = store.similarity_search("embedded seekdb", k=1)
    assert results[0].metadata["source"] == "embedded"


def test_embedded_seekdb_add_and_retrieve(tmp_path: Path) -> None:
    seekdb_path = Path(tempfile.mkdtemp(prefix="agentseek-seekdb-", dir="/tmp"))
    source_root = Path(__file__).resolve().parents[1] / "src"
    try:
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(Path(__file__).resolve()), str(seekdb_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=tmp_path,
            env={
                **os.environ,
                "SEEKDB_PATH": str(seekdb_path),
                "PYTHONPATH": str(source_root),
            },
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        shutil.rmtree(seekdb_path, ignore_errors=True)


if __name__ == "__main__":
    _run_smoke(Path(sys.argv[1]))
