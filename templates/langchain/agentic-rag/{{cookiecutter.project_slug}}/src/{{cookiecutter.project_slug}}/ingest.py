"""Document ingestion CLI.

Usage:
    uv run ingest path/to/docs/
    uv run ingest https://example.com
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_oceanbase.embedding_utils import DefaultEmbeddingFunctionAdapter
from langchain_oceanbase.vectorstores import OceanbaseVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

EMBEDDING_DIM = 384

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)


def _get_vector_store() -> OceanbaseVectorStore:
    return OceanbaseVectorStore(
        embedding_function=DefaultEmbeddingFunctionAdapter(),
        table_name=os.getenv("VECTOR_TABLE_NAME", "{{ cookiecutter.vector_table_name }}"),
        connection_args={
            "host": os.getenv("SEEKDB_HOST", "127.0.0.1"),
            "port": os.getenv("SEEKDB_PORT", "2881"),
            "user": os.getenv("SEEKDB_USER", "root"),
            "password": os.getenv("SEEKDB_PASSWORD", ""),
            "db_name": os.getenv("SEEKDB_DB_NAME", "test"),
        },
        vidx_metric_type="l2",
        embedding_dim=EMBEDDING_DIM,
    )


def load_directory(directory: Path) -> list[Document]:
    docs: list[Document] = []
    for filepath in sorted(directory.rglob("*")):
        if filepath.suffix in (".txt", ".md") and filepath.is_file():
            content = filepath.read_text(encoding="utf-8")
            docs.append(Document(page_content=content, metadata={"source": str(filepath)}))
    return docs


def load_url(url: str) -> list[Document]:
    import bs4
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return [Document(page_content=text, metadata={"source": url})]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ingest <path-or-url> [path-or-url ...]")
        sys.exit(1)

    all_docs: list[Document] = []
    for arg in sys.argv[1:]:
        if arg.startswith("http://") or arg.startswith("https://"):
            print(f"Loading URL: {arg}")
            all_docs.extend(load_url(arg))
        else:
            p = Path(arg)
            if p.is_dir():
                print(f"Loading directory: {p}")
                all_docs.extend(load_directory(p))
            elif p.is_file():
                print(f"Loading file: {p}")
                content = p.read_text(encoding="utf-8")
                all_docs.append(Document(page_content=content, metadata={"source": str(p)}))
            else:
                print(f"Skipping (not found): {arg}")

    if not all_docs:
        print("No documents loaded.")
        sys.exit(1)

    splits = text_splitter.split_documents(all_docs)
    print(f"Split {len(all_docs)} document(s) into {len(splits)} chunks.")

    vector_store = _get_vector_store()
    ids = vector_store.add_documents(splits)
    print(f"Indexed {len(ids)} chunks into table '{vector_store.table_name}'.")


if __name__ == "__main__":
    main()
