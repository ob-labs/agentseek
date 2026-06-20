"""Document ingestion CLI — builds a FAISS index with OpenVINO embeddings.

Usage:
    uv run ingest path/to/docs/
    uv run ingest https://example.com
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .ov_models import OpenVINOEmbeddings

load_dotenv()

EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "{{ cookiecutter.embedding_model_path }}")
DEVICE = os.getenv("OPENVINO_DEVICE", "{{ cookiecutter.device }}")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)


def load_directory(directory: Path) -> list[Document]:
    docs: list[Document] = []
    for filepath in sorted(directory.rglob("*")):
        if filepath.suffix in (".txt", ".md", ".pdf") and filepath.is_file():
            if filepath.suffix == ".pdf":
                docs.extend(_load_pdf(filepath))
            else:
                content = filepath.read_text(encoding="utf-8")
                docs.append(Document(page_content=content, metadata={"source": str(filepath)}))
    return docs


def _load_pdf(path: Path) -> list[Document]:
    from langchain_community.document_loaders import PyPDFLoader

    return PyPDFLoader(str(path)).load()


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
                if p.suffix == ".pdf":
                    all_docs.extend(_load_pdf(p))
                else:
                    content = p.read_text(encoding="utf-8")
                    all_docs.append(Document(page_content=content, metadata={"source": str(p)}))
            else:
                print(f"Skipping (not found): {arg}")

    if not all_docs:
        print("No documents loaded.")
        sys.exit(1)

    splits = text_splitter.split_documents(all_docs)
    print(f"Split {len(all_docs)} document(s) into {len(splits)} chunks.")

    embeddings = OpenVINOEmbeddings.from_model_path(EMBEDDING_MODEL_PATH, device=DEVICE)

    index_path = Path(FAISS_INDEX_PATH)
    if index_path.exists():
        print(f"Loading existing index from {index_path}")
        db = FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)
        db.add_documents(splits)
    else:
        db = FAISS.from_documents(splits, embeddings)

    db.save_local(str(index_path))
    print(f"Indexed {len(splits)} chunks into {index_path}/")


if __name__ == "__main__":
    main()
