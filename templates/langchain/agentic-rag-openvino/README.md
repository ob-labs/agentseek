# langchain/agentic-rag-openvino

Cookiecutter template for an **agentic RAG** application running entirely on
local hardware using [OpenVINO](https://docs.openvino.ai/) for LLM inference,
embeddings, and reranking — no cloud API keys required.

The generated project includes:

- **Backend** — a `create_agent` graph with a retrieval tool backed by FAISS,
  served by `langgraph dev`. The agent autonomously decides when and how many
  times to search the knowledge base.
- **Frontend** — React + Vite chat UI with streaming tool-call cards and
  markdown rendering via `@langchain/react` `useStream`.
- **Ingest CLI** — `uv run ingest` loads documents from files, directories,
  or URLs, chunks them, and indexes into FAISS.
- **Model converter** — `uv run convert-models` downloads HuggingFace models
  and exports them to OpenVINO IR with INT4/INT8 weight compression.

## Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/)
- **Linux or macOS** (OpenVINO GenAI runs on x86_64; ARM via Rosetta on macOS)
- **8+ GB RAM** (16 GB recommended for larger models)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick start

```bash
# 1. Scaffold
uvx cookiecutter templates/langchain/agentic-rag-openvino

# 2. Setup
cd <project_slug>
cp .env.example .env
uv sync
uv run convert-models        # download + convert models (~15 min first time)

# 3. Ingest
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/

# 4. Backend
uv run langgraph dev

# 5. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Cookiecutter variables

| Variable | Default | Description |
| --- | --- | --- |
| `project_name` | My OpenVINO RAG Agent | Human-readable project name |
| `project_slug` | *(derived)* | Python package / directory name |
| `author` | Your Name | Author for pyproject.toml |
| `llm_model_path` | ./models/tiny-llama-1b-chat/INT4_compressed_weights | Path to OpenVINO LLM |
| `embedding_model_path` | ./models/bge-small-en-v1.5 | Path to OpenVINO embedding model |
| `rerank_model_path` | ./models/bge-reranker-v2-m3 | Path to reranker (empty to disable) |
| `device` | CPU | OpenVINO device: CPU, GPU, or NPU |
| `vector_table_name` | rag_documents | FAISS index directory name |
| `frontend_port` | 5174 | Frontend Vite dev server port |

## Generated layout

```text
{{ project_slug }}/
  README.md
  pyproject.toml
  langgraph.json
  .env.example
  models/                    (created by convert-models)
  faiss_index/               (created by ingest)
  src/{{ project_slug }}/
    __init__.py
    agent.py
    ingest.py
    convert_models.py
    ov_models.py
  frontend/
    package.json
    index.html
    vite.config.ts
    tsconfig.json
    src/
      App.tsx
      ToolCallCard.tsx
      main.tsx
      styles.css
      vite-env.d.ts
```

## Design decisions

- Uses OpenVINO GenAI `LLMPipeline` for streaming LLM inference — simple
  `from_model_path(dir, device)` API, no PyTorch runtime needed.
- Uses `TextEmbeddingPipeline` for embeddings — same pattern as the LLM.
- Reranking is optional — if `RERANK_MODEL_PATH` points to a valid directory,
  the reranker loads; otherwise retrieval uses raw similarity scores.
- FAISS for vector storage — lightweight, no external service needed, indexes
  persist to disk.
- `convert_models.py` wraps `optimum-cli export openvino` so users don't need
  to remember CLI flags.
- INT4 weight compression by default for the LLM (best speed/quality tradeoff
  on CPU); embedding and reranker models stay at FP32/FP16.
- Supports CPU, GPU (Intel Arc / iGPU), and NPU (Intel Core Ultra) via the
  `OPENVINO_DEVICE` env var.
