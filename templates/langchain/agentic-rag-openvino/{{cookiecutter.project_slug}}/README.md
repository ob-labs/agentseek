# {{ cookiecutter.project_name }}

LangChain agentic RAG running entirely on local hardware with
[OpenVINO](https://docs.openvino.ai/) — no cloud API keys required.

Scaffolded with `agentseek create langchain/agentic-rag-openvino`.

The backend serves a `create_agent(...)` graph through `langgraph dev`.
All inference (LLM, embeddings, reranking) runs locally via OpenVINO GenAI.
The frontend streams user messages, tool calls (retrieval), and the final
markdown answer.

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

This downloads and converts three models to OpenVINO IR format:

| Model | Purpose | Size |
| --- | --- | --- |
| TinyLlama-1.1B-Chat (INT4) | LLM generation | ~700 MB |
| bge-small-en-v1.5 | Embeddings (384-dim) | ~130 MB |
| bge-reranker-v2-m3 | Reranking (optional) | ~1.1 GB |

To use a different LLM (e.g. Llama-3, Phi-3, Qwen2), convert it manually:

```bash
optimum-cli export openvino --model <hf-model-id> --task text-generation-with-past --weight-format int4 ./models/<name>/INT4_compressed_weights
```

Then update `LLM_MODEL_PATH` in `.env`.

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env if you changed model paths or want to enable LangSmith tracing
```

## Ingest

Before running the agent, ingest documents into the FAISS index:

```bash
# Web pages
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/

# Local files (.txt, .md, .pdf) or directories
uv run ingest ./docs/

# Multiple sources at once
uv run ingest ./notes/ https://example.com/article ./paper.pdf
```

Documents are split into 1000-character chunks with 200-character overlap,
embedded locally via bge-small-en-v1.5 (384-dim), and stored in a FAISS index.

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

- A **Tool: retrieve** card appears while the agent searches the knowledge base.
- The card collapses with a "DONE" badge after retrieval completes.
- The final assistant response renders as markdown.

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
