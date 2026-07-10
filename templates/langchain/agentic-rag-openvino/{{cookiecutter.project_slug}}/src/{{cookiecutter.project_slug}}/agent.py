"""Local OpenVINO RAG graph, served by `langgraph dev`."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_oceanbase.vectorstores import OceanbaseVectorStore
from langgraph.graph import MessagesState, StateGraph

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
        f"Cannot connect to OceanBase seekdb at {SEEKDB_HOST}:{SEEKDB_PORT}. "
        "Did you run `docker compose up -d`?  "
        f"Original error: {exc}"
    ) from exc


def retrieve(query: str) -> tuple[str, list]:
    """Retrieve relevant documents from the knowledge base."""
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


def _latest_human_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage) or getattr(message, "type", "") == "human":
            return str(message.content)
    return ""


def _text_from_generation(result: object) -> str:
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(part) for part in content)
    return str(content)


def answer(state: MessagesState) -> dict:
    """Run deterministic retrieve-then-generate RAG with the local OpenVINO LLM."""
    query = _latest_human_text(state["messages"])
    context, _docs = retrieve(query)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "Answer the user's question using only the retrieved context below. "
        "If the context does not contain the answer, say you don't know.\n\n"
        f"Retrieved context:\n{context or '(no relevant documents retrieved)'}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )
    response = _text_from_generation(ov_llm.invoke(prompt)).strip()
    return {"messages": [AIMessage(content=response)]}


graph = StateGraph(MessagesState).add_node("answer", answer).set_entry_point("answer").compile()
