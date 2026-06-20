"""LangChain RAG graph with 3 OpenVINO models + OceanBase/SeekDB vector store."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_oceanbase.vectorstores import OceanbaseVectorStore
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from .ov_models import OpenVINOEmbeddings, OpenVINOLLM, OpenVINOReranker

load_dotenv()

RAG_PROMPT = """{{ cookiecutter.system_prompt }}

Context:
{context}

Question: {question}

Answer:"""

LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "{{ cookiecutter.llm_model_path }}")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "{{ cookiecutter.embedding_model_path }}")
RERANK_MODEL_PATH = os.getenv("RERANK_MODEL_PATH", "{{ cookiecutter.rerank_model_path }}")
DEVICE = os.getenv("OPENVINO_DEVICE", "{{ cookiecutter.device }}")

SEEKDB_HOST = os.getenv("SEEKDB_HOST", "127.0.0.1")
SEEKDB_PORT = os.getenv("SEEKDB_PORT", "2881")
SEEKDB_USER = os.getenv("SEEKDB_USER", "root@test")
SEEKDB_PASSWORD = os.getenv("SEEKDB_PASSWORD", "")
SEEKDB_DB_NAME = os.getenv("SEEKDB_DB_NAME", "{{ cookiecutter.seekdb_db_name }}")
VECTOR_TABLE_NAME = os.getenv("VECTOR_TABLE_NAME", "{{ cookiecutter.vector_table_name }}")

embeddings = OpenVINOEmbeddings.from_model_path(EMBEDDING_MODEL_PATH, device=DEVICE)

EMBEDDING_DIM = len(embeddings.embed_query("dim"))

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
    embedding_dim=EMBEDDING_DIM,
)

reranker = None
if RERANK_MODEL_PATH and os.path.isdir(RERANK_MODEL_PATH):
    reranker = OpenVINOReranker.from_model_path(RERANK_MODEL_PATH, device=DEVICE, top_n=3)

llm = OpenVINOLLM.from_model_path(LLM_MODEL_PATH, device=DEVICE)
llm.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "512"))

prompt_template = PromptTemplate.from_template(RAG_PROMPT)


class RAGState(TypedDict):
    messages: list[dict[str, Any]]
    context: str
    answer: str


def retrieve_node(state: RAGState, config: RunnableConfig) -> dict:
    """Retrieve relevant documents for the last user message."""
    messages = state["messages"]
    query = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            query = msg["content"]
            break
        elif hasattr(msg, "type") and msg.type == "human":
            query = msg.content
            break

    docs = vector_store.similarity_search(query, k=6 if reranker else 4)
    if reranker:
        docs = list(reranker.compress_documents(docs, query))

    context = "\n\n".join(doc.page_content for doc in docs)
    return {"context": context}


def generate_node(state: RAGState, config: RunnableConfig) -> dict:
    """Generate answer using retrieved context."""
    messages = state["messages"]
    query = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            query = msg["content"]
            break
        elif hasattr(msg, "type") and msg.type == "human":
            query = msg.content
            break

    filled_prompt = prompt_template.format(context=state["context"], question=query)
    answer = llm.invoke(filled_prompt)
    return {
        "answer": answer,
        "messages": messages + [{"role": "assistant", "content": answer}],
    }


builder = StateGraph(RAGState)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()
