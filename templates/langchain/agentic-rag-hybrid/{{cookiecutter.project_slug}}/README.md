# {{ cookiecutter.project_name }}

Agentic hybrid RAG over an image-backed knowledge base. The generated app helps developers see how vector, sparse-token, exact full-text, metadata, and fused hybrid retrieval behave against the same images.

## Prerequisites

- Python and `uv`
- Node.js and `npm`
- Docker, only when you want the optional Phoenix tracing stack
- A SiliconFlow-compatible API key for chat, text/image embeddings, and optional VLM captions

## Configure

```bash
cp .env.example .env
$EDITOR .env
```

Set the canonical AgentSeek model settings first:

```env
AGENTSEEK_MODEL_PROVIDER={{ cookiecutter.default_model_provider }}
AGENTSEEK_MODEL={{ cookiecutter.default_model }}
AGENTSEEK_API_KEY=sk-...
AGENTSEEK_API_BASE=https://api.siliconflow.cn/v1
```

`AGENTSEEK_API_KEY` feeds chat, image/text embeddings, and optional VLM captioning by default. Existing `SILICONFLOW_API_KEY` and `OPENAI_API_KEY` shell exports still work as compatibility aliases; use `EMBEDDING_API_KEY` or `VLM_API_KEY` only when those paths need separate credentials.

By default, `SEEKDB_PATH` and `MEDIA_DATA_DIR` live under `~/.agentseek/hybrid-rag/{{ cookiecutter.project_slug }}/` so LangGraph dev does not reload while DB, index, upload, or thumbnail files are changing.

## Setup

Run setup through AgentSeek lifecycle tasks:

```bash
agentseek task sync
agentseek task frontend
agentseek task seekdb
agentseek task ingest-sample
agentseek doctor
agentseek dev
```

Open the frontend shown by `agentseek info` and start with the Guided Lab tab. It indexes a photo-style starter pack with product, shipping, document, bottle, safety-sign, and near-miss examples. The Lab and Compare tabs show vector, sparse-token, exact full-text, metadata, and fused results side by side.

The starter pack is a source-tree demo fixture under `examples/sample_pack/`, not Python package data. Keep the generated project directory intact when running lifecycle tasks, `uv run ingest-images`, `uv run hybrid-demo`, or the sample-pack custom routes.

## Service Entry Points

- LangGraph backend: `http://127.0.0.1:2024`
- React frontend: `http://127.0.0.1:{{ cookiecutter.frontend_port }}`
- Custom route health check: `http://127.0.0.1:2024/custom/health`
- Phoenix, when started: `http://127.0.0.1:6006`

For trusted remote development, bind both servers explicitly:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```

The frontend derives the backend host from the browser location by default. If you serve it behind a different public origin, set `VITE_LANGGRAPH_API_URL` and `VITE_CUSTOM_ROUTES_URL` for the frontend process.

## Knowledge Ingestion

`agentseek task ingest-sample` loads the built-in sample pack. You can also run:

```bash
uv run ingest-images
uv run hybrid-demo
```

The ingest command stages captions through a LangChain `Embeddings` adapter, embeds PNG files through the SiliconFlow multimodal image embedding path, and writes records through `langchain-oceanbase` `OceanbaseVectorStore` in embedded OceanBase seekdb mode. The demo embeds each query through the SiliconFlow text embedding path, then runs the same query through `semantic`, `keyword`, `exact`, and `balanced` modes.

## Verification

The generated test suite includes a deterministic integration proof that creates the real `langchain-oceanbase` `OceanbaseVectorStore` through `HybridImageStore`, writes two captioned image fixtures to a temporary embedded seekdb path, verifies their managed media copies, and retrieves the expected image with a text query. It injects a small local deterministic embedding engine, so this test makes no hosted or network calls:

```bash
uv sync --extra dev
uv run python -m pytest
cd frontend
npm install
npm run build
```

The hybrid template CI smoke runs that full Python suite and the frontend production build. It does not call SiliconFlow models and does not prove a live Phoenix deployment.

Credentialed live proof is separate: configure a real `AGENTSEEK_API_KEY`, run `agentseek task ingest-sample` and `uv run hybrid-demo` for hosted SiliconFlow embeddings, then start and enable Phoenix as described below to inspect exported traces. Those steps validate external credentials, model behavior, and the optional observability stack beyond the deterministic CI contract.

## Phoenix Observability

The template can export LangChain/LangGraph spans to a local Phoenix instance using the same AgentSeek Phoenix image as the default LangChain template. Phoenix trace storage is backed by OceanBase seekdb through `docker-compose.yml`; this tracing database is separate from the embedded `SEEKDB_PATH` used by hybrid retrieval.

```bash
agentseek task phoenix
```

Then enable OTEL in `.env` before starting `agentseek dev`:

```env
AGENTSEEK_OTEL_ENABLED=true
AGENTSEEK_OTEL_SERVICE_NAME={{ cookiecutter.project_slug }}
AGENTSEEK_OTEL_PROJECT_NAME={{ cookiecutter.project_slug }}
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:6006/v1/traces
```

Open Phoenix at `http://127.0.0.1:6006`. The custom route `http://127.0.0.1:2024/custom/observability` shows the active OTEL endpoint, service name, Phoenix URL, and OceanBase seekdb URL.

With OTEL enabled, the Lab and Compare tabs invoke LangChain runnable wrappers for sample-pack ingest, archive upload, and compare-mode retrieval, so Phoenix records those flows through the same LangChain instrumentation used by the Ask tab. The Ask tab emits the LangGraph agent run, model calls, and `hybrid_search_knowledge_base` tool span.

LangSmith environment variables are accepted by LangChain if you set them, but Phoenix is the documented local tracing backend for this template.

## Agent Skills

`agentseek task seekdb-skills` runs `npx skills add oceanbase/seekdb-ecology-plugins --all` to install recommended OceanBase seekdb skills for supported coding agents. This uses the external `skills` tooling; `agentseek task --list` remains the canonical way to discover template tasks.

## What This Template Teaches

- Vector search finds visually or semantically similar records.
- Sparse/keyword search rewards important words in captions.
- Full-text search is best for exact labels and names.
- Metadata search rewards file names, tags, and source metadata.
- Hybrid search fuses the routes so mixed queries do not depend on one retrieval strategy.
- Agent middleware teaches the model when to choose `semantic`, `keyword`, `exact`, or `balanced`.
- LangGraph custom routes expose upload, image serving, and compare-mode diagnostics on the same dev server as the graph.
- Phoenix observability can show LangChain-instrumented Lab and Compare retrieval runs, the agent run, model calls, and hybrid-search tool span while storing traces in OceanBase seekdb.
- The frontend Lab tab ships with photo-style fixtures, visible in-image text, guided cases, and visual rank comparisons so developers can test hybrid behavior immediately.

## Local Models

This template does not prepare local model artifacts. Chat, embeddings, and VLM captioning use hosted OpenAI-compatible endpoints by default. If you add local models later, add a `models` lifecycle task and document device/artifact preparation.

## Design Notes

The implementation uses `langchain-oceanbase` as the storage/search infrastructure. Image vectors, hashed sparse token vectors, full-text content, captions, tags, and metadata are written through `OceanbaseVectorStore` with embedded seekdb enabled by `SEEKDB_PATH`. The app intentionally keeps vector, sparse, full-text, and metadata routes visible in the Lab tab so developers can see how each retrieval signal changes the fused rank.

Phoenix tracing follows the AgentSeek Phoenix compose convention: `AGENTSEEK_PHOENIX_IMAGE` defaults to `ghcr.io/agentseek-ai/agentseek-phoenix:main`, and `OCEANBASE_SEEKDB_IMAGE` defaults to `quay.io/oceanbase/seekdb:latest`.
