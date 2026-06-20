# langchain/agentic-rag-openvino

Cookiecutter template for an **agentic RAG** application running fully local
with 3 [OpenVINO](https://docs.openvino.ai/) models and
[OceanBase/SeekDB](https://github.com/oceanbase/seekdb) as the vector store.
No cloud API keys required.

## Models

The generated project uses 3 OpenVINO models converted from HuggingFace via
[Optimum Intel](https://huggingface.co/docs/optimum/intel/index):

| Role | Default Model | OpenVINO API | Purpose |
| --- | --- | --- | --- |
| **LLM** | TinyLlama-1.1B-Chat (INT4) | `LLMPipeline` | Answer generation |
| **Embeddings** | bge-small-en-v1.5 (FP32) | `TextEmbeddingPipeline` | 384-dim document/query vectors |
| **Reranker** | bge-reranker-v2-m3 (FP32) | compiled cross-encoder | Re-score retrieved documents |

All models are swappable — convert any HuggingFace model with `optimum-cli`
and point the env var at the new directory.

## What's generated

- **Backend** — a retrieve→generate `StateGraph` served by `langgraph dev`.
  Embedding + reranking + LLM all run via OpenVINO GenAI on local hardware.
- **Frontend** — React + Vite chat UI with streaming via `@langchain/react`
  `useStream`.
- **Ingest CLI** — `uv run ingest` loads documents from files, directories,
  or URLs, chunks them, embeds with OpenVINO, and indexes into SeekDB.
- **Model converter** — `uv run convert-models` downloads 3 HuggingFace models
  and exports them to OpenVINO IR format.

## Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/)
- **Linux x86_64** (primary) or macOS x86_64 (via Rosetta)
- **8+ GB RAM** (16 GB recommended for larger models)
- **Docker** (for SeekDB) or Linux with pylibseekdb embedded mode

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

# 3. Convert models (downloads ~2 GB, takes ~15 min first time)
uv run convert-models

# 4. Start SeekDB
docker compose up -d

# 5. Ingest documents
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/

# 6. Backend
uv run langgraph dev

# 7. Frontend (separate terminal)
cd frontend && npm install && npm run dev
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
| `seekdb_db_name` | test | SeekDB database name |
| `vector_table_name` | rag_documents | Vector store table name |
| `frontend_port` | 5174 | Frontend Vite dev server port |

## Generated layout

```text
{{ project_slug }}/
  README.md
  pyproject.toml
  langgraph.json
  docker-compose.yml
  .env.example
  models/                    (created by convert-models)
    tiny-llama-1b-chat/INT4_compressed_weights/
    bge-small-en-v1.5/
    bge-reranker-v2-m3/
  src/{{ project_slug }}/
    __init__.py
    agent.py                 (RAG graph: retrieve → generate)
    ingest.py                (document ingestion CLI)
    convert_models.py        (model download + conversion)
    ov_models.py             (OpenVINO LangChain wrappers)
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

- **3 OpenVINO models**: LLM (`LLMPipeline`), embeddings
  (`TextEmbeddingPipeline`), reranker (compiled `openvino_model.xml` with
  `openvino_genai.Tokenizer`). All load from a directory path + device string.
- **OceanBase/SeekDB** for vector storage: production-grade distributed vector
  DB, same as the `langchain/agentic-rag` template.
- **`optimum-cli export openvino`** for model conversion: standard HuggingFace
  tooling, supports INT4/INT8/FP16 weight compression.
- **Retrieve→generate StateGraph** instead of `create_agent`: local LLMs
  (especially small ones) don't reliably support tool-calling, so we use a
  fixed two-step graph that always retrieves before generating.
- **INT4 for LLM, FP32 for embedding/reranker**: LLM benefits most from
  compression (speed + memory); embedding quality degrades with quantization.
- **Supports CPU, GPU, NPU** via a single `OPENVINO_DEVICE` env var.
- **No PyTorch at runtime**: only `openvino` and `openvino-genai` are needed
  for inference. PyTorch/optimum are only used during model conversion.
