# langchain/agentic-rag-openvino

Cookiecutter template for a local RAG application running fully local
with [OpenVINO](https://docs.openvino.ai/) via LangChain's official
[langchain-huggingface](https://python.langchain.com/docs/integrations/llms/openvino)
integration and [OceanBase seekdb](https://github.com/oceanbase/seekdb) as the
vector store. No cloud API keys required.

The generated graph uses a deterministic retrieve-then-generate graph instead
of `create_agent` tool-calling. Local Hugging Face/OpenVINO pipelines are kept
on the stable LLM path while retrieval stays explicit and predictable.

## How it integrates

```python
from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings
from langgraph.graph import MessagesState, StateGraph

# LLM: HuggingFacePipeline with backend="openvino"
ov_llm = HuggingFacePipeline.from_model_id(
    model_id="./models/tiny-llama/INT4", task="text-generation",
    backend="openvino", model_kwargs={"device": "CPU"},
)

# Embeddings: HuggingFaceEmbeddings with backend="openvino"
embeddings = HuggingFaceEmbeddings(
    model_name="./models/bge-small-en-v1.5",
    model_kwargs={"device": "cpu", "backend": "openvino"},
)

# Deterministic graph pattern
graph = StateGraph(MessagesState).add_node("answer", answer).set_entry_point("answer").compile()
```

## What's generated

- **Backend** — a deterministic retrieve-then-generate graph backed by
  `OceanbaseVectorStore`, served by `langgraph dev`.
- **Frontend** — React + Vite chat UI with streaming tool-call cards and
  markdown rendering via `@langchain/react` `useStream`.
- **Ingest CLI** — `uv run ingest` loads documents, embeds with OpenVINO, and
  indexes into OceanBase seekdb.
- **Model converter** — `uv run convert-models` downloads HuggingFace models
  and exports them to OpenVINO IR with INT4/INT8 weight compression.

## Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** with npm (for the Vite frontend)
- **Linux x86_64** (primary) or macOS x86_64 (via Rosetta)
- **8+ GB RAM** (16 GB recommended for larger models)
- **Docker** (for OceanBase seekdb)

## Quick start

```bash
uv tool install agentseek                              # install the agentseek CLI once
agentseek create langchain/agentic-rag-openvino        # scaffold the project
cd <project_slug>
cp .env.example .env
uv sync
agentseek info
agentseek task frontend      # install frontend dependencies
agentseek doctor             # static lifecycle checks
agentseek task models        # download + convert models (~15 min)
agentseek task seekdb        # start OceanBase seekdb in the background
agentseek task ingest-sample
agentseek dev                # OceanBase seekdb + backend + frontend
```

Use `agentseek dev --dry-run` to inspect the startup plan, `agentseek task --list`
to see one-shot setup tasks, and `agentseek doctor --live` after `agentseek dev`
is running to check the declared HTTP endpoints.

## Cookiecutter variables

| Variable | Default | Description |
| --- | --- | --- |
| `project_name` | My OpenVINO RAG Agent | Human-readable project name |
| `project_slug` | *(derived)* | Python package / directory name |
| `llm_model_path` | ./models/tiny-llama-1b-chat/INT4_compressed_weights | Path to OpenVINO LLM |
| `embedding_model_path` | ./models/bge-small-en-v1.5 | Path to OpenVINO embedding model |
| `device` | CPU | OpenVINO device: CPU, GPU, or NPU |
| `seekdb_db_name` | test | OceanBase seekdb database name |
| `vector_table_name` | rag_documents | Vector store table name |
| `frontend_port` | 5174 | Frontend Vite dev server port |

## Design decisions

- **Official LangChain integration**: uses `langchain-huggingface` with
  `backend="openvino"` for both LLM and embeddings — standard, maintained,
  documented.
- **Deterministic graph instead of tool-calling**: local OpenVINO inference
  uses `HuggingFacePipeline` directly, retrieves first, then generates from the
  retrieved context. Use the cloud `langchain/agentic-rag` template when you
  need autonomous tool-calling.
- **`optimum-cli export openvino`** for model conversion: standard HuggingFace
  tooling, supports INT4/INT8/FP16 weight compression.
- **OceanBase seekdb** for vector storage: same production-grade DB as the
  cloud template.
- **INT4 for LLM, FP32 for embeddings**: LLM benefits most from compression;
  embedding quality degrades with quantization.
- **Supports CPU, GPU, NPU** via `OPENVINO_DEVICE` env var.
- **PyTorch in the venv** (via `optimum[openvino]`) is used only for model
  conversion (`convert-models`). At runtime, `langchain-huggingface` uses
  optimum-intel which does import torch. The generated README documents an
  alternative `openvino-genai` path that avoids torch at runtime and adds
  native reranking — see "Advanced" section.
