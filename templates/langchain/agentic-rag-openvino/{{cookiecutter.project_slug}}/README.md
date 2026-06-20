# {{ cookiecutter.project_name }}

LangChain RAG with local [OpenVINO](https://docs.openvino.ai/) LLM inference
and [OceanBase/SeekDB](https://github.com/oceanbase/seekdb) vector store with
seekdb embed (384-dim, no API key).

Scaffolded with `agentseek create langchain/agentic-rag-openvino`.

The backend serves a retrieve→generate graph through `langgraph dev`.
LLM generation runs locally via OpenVINO GenAI (no cloud API keys).
Embeddings use seekdb embed (built into langchain-oceanbase).
The frontend streams the RAG workflow with tool-call cards.

## Setup

### 1. Install dependencies

```bash
uv sync
npm install --prefix frontend
```

### 2. Download and convert models

```bash
uv run convert-models
```

This downloads and converts:

| Model | Purpose | Size |
| --- | --- | --- |
| TinyLlama-1.1B-Chat (INT4) | LLM generation | ~700 MB |
| bge-reranker-v2-m3 | Reranking (optional) | ~1.1 GB |

To use a different LLM (e.g. Phi-3, Qwen2), convert it manually:

```bash
optimum-cli export openvino --model <hf-model-id> --task text-generation-with-past --weight-format int4 ./models/<name>/INT4_compressed_weights
```

Then update `LLM_MODEL_PATH` in `.env`.

### 3. Start SeekDB

```bash
docker compose up -d        # wait ~60s on first run
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if you changed model paths or want to enable LangSmith tracing
```

## Ingest

Before running the agent, ingest documents into the knowledge base:

```bash
# Web pages
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/

# Local files (.txt, .md, .pdf) or directories
uv run ingest ./docs/

# Multiple sources at once
uv run ingest ./notes/ https://example.com/article ./paper.pdf
```

Documents are split into 1000-character chunks with 200-character overlap,
embedded via seekdb embed (384-dim, no API key), and indexed into SeekDB.

## Run

Start the backend:

```bash
uv run langgraph dev --no-browser
```

Start the frontend in a second terminal:

```bash
npm run --prefix frontend dev
```

By default the backend listens on `http://127.0.0.1:2024` and the frontend on
`http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
What is task decomposition?
```

Expected behavior:

- The **retrieve** step searches the knowledge base.
- The **generate** step produces an answer grounded in the retrieved context.
- The final response renders as markdown.

## Hardware requirements

- **Minimum**: 8 GB RAM, any x86_64 CPU with AVX2 (Intel 4th gen+, AMD Zen+)
- **Recommended**: 16 GB RAM, Intel Core Ultra / Xeon with AMX for best throughput
- **GPU acceleration**: Set `OPENVINO_DEVICE=GPU` with Intel Arc/iGPU
- **NPU acceleration**: Set `OPENVINO_DEVICE=NPU` on Intel Core Ultra laptops

## Using larger models

For better quality, swap the LLM to a larger model:

```bash
# Example: Phi-3-mini (3.8B params, INT4 ~2.2 GB)
optimum-cli export openvino \
  --model microsoft/Phi-3-mini-4k-instruct \
  --task text-generation-with-past \
  --weight-format int4 \
  ./models/phi-3-mini/INT4_compressed_weights

# Update .env
LLM_MODEL_PATH=./models/phi-3-mini/INT4_compressed_weights
```
