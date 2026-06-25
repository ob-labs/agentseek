"""LangChain agentic RAG with OpenVINO local models, served by `langgraph dev`."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_oceanbase.vectorstores import OceanbaseVectorStore

load_dotenv()

SYSTEM_PROMPT = "{{ cookiecutter.system_prompt }}"

LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "{{ cookiecutter.llm_model_path }}")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "{{ cookiecutter.embedding_model_path }}")
DEVICE = os.getenv("OPENVINO_DEVICE", "{{ cookiecutter.device }}")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))

SEEKDB_HOST = os.getenv("SEEKDB_HOST", "127.0.0.1")
SEEKDB_PORT = os.getenv("SEEKDB_PORT", "2881")
SEEKDB_USER = os.getenv("SEEKDB_USER", "root")
SEEKDB_PASSWORD = os.getenv("SEEKDB_PASSWORD", "")
SEEKDB_DB_NAME = os.getenv("SEEKDB_DB_NAME", "{{ cookiecutter.seekdb_db_name }}")
VECTOR_TABLE_NAME = os.getenv("VECTOR_TABLE_NAME", "{{ cookiecutter.vector_table_name }}")

# --- Embeddings (OpenVINO backend) ---
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_PATH,
    model_kwargs={"device": "cpu", "backend": "openvino"},
)

_embedding_dim: int | None = None


def _get_embedding_dim() -> int:
    """Lazily compute embedding dimension to avoid inference at import time."""
    global _embedding_dim
    if _embedding_dim is None:
        _embedding_dim = len(embeddings.embed_query("dim"))
    return _embedding_dim


# --- Vector store ---
try:
    vector_store = OceanbaseVectorStore(
        embedding_function=embeddings,
        table_name=VECTOR_TABLE_NAME,
        connection_args={
            "host": SEEKDB_HOST,
            "port": SEEKDB_PORT,
            "user": SEEKDB_USER,
            "password": SEEKDB_PASSWORD,
            "db_name": SEEKDB_DB_NAME,
        },
        vidx_metric_type="l2",
        embedding_dim=_get_embedding_dim(),
    )
except Exception as exc:
    raise ConnectionError(
        f"Cannot connect to SeekDB at {SEEKDB_HOST}:{SEEKDB_PORT}. "
        "Did you run `docker compose up -d`?  "
        f"Original error: {exc}"
    ) from exc


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve relevant documents from the knowledge base to answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=4)
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# --- LLM (OpenVINO backend) ---
ov_llm = HuggingFacePipeline.from_model_id(
    model_id=LLM_MODEL_PATH,
    task="text-generation",
    backend="openvino",
    model_kwargs={"device": DEVICE},
    pipeline_kwargs={"max_new_tokens": MAX_NEW_TOKENS},
)
model = ChatHuggingFace(llm=ov_llm)

graph = create_agent(
    model=model,
    tools=[retrieve],
    system_prompt=SYSTEM_PROMPT,
)
