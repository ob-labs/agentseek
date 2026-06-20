"""LangChain agentic RAG graph with OpenVINO local models, served by `langgraph dev`."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.vectorstores import FAISS

from .ov_models import OpenVINOEmbeddings, OpenVINOLLM, OpenVINOReranker

load_dotenv()

SYSTEM_PROMPT = "{{ cookiecutter.system_prompt }}"

LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "{{ cookiecutter.llm_model_path }}")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "{{ cookiecutter.embedding_model_path }}")
RERANK_MODEL_PATH = os.getenv("RERANK_MODEL_PATH", "{{ cookiecutter.rerank_model_path }}")
DEVICE = os.getenv("OPENVINO_DEVICE", "{{ cookiecutter.device }}")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index")

embeddings = OpenVINOEmbeddings.from_model_path(EMBEDDING_MODEL_PATH, device=DEVICE)

reranker = None
if RERANK_MODEL_PATH and os.path.isdir(RERANK_MODEL_PATH):
    reranker = OpenVINOReranker.from_model_path(RERANK_MODEL_PATH, device=DEVICE, top_n=3)

vector_store = FAISS.load_local(
    FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
)


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve relevant documents from the knowledge base to answer a query."""
    docs = vector_store.similarity_search(query, k=6 if reranker else 4)
    if reranker:
        docs = list(reranker.compress_documents(docs, query))
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}" for doc in docs
    )
    return serialized, docs


llm = OpenVINOLLM.from_model_path(LLM_MODEL_PATH, device=DEVICE)
llm.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "512"))

graph = create_agent(
    model=llm,
    tools=[retrieve],
    system_prompt=SYSTEM_PROMPT,
)
