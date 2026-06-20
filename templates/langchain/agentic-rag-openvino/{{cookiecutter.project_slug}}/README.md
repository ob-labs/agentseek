# {{ cookiecutter.project_name }}

LangChain RAG running **fully local** with 3 [OpenVINO](https://docs.openvino.ai/)
models for inference and [OceanBase/SeekDB](https://github.com/oceanbase/seekdb)
as the vector store. No cloud API keys required.

Scaffolded with `agentseek create langchain/agentic-rag-openvino`.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  All inference runs locally via OpenVINO GenAI           │
├─────────────────────────────────────────────────────────┤
│  Embedding:  bge-small-en-v1.5    (384-dim vectors)     │
│  Reranker:   bge-reranker-v2-m3   (cross-encoder)       │
│  LLM:        TinyLlama-1.1B-Chat  (INT4 compressed)     │
├─────────────────────────────────────────────────────────┤
│  Vector DB:  OceanBase/SeekDB (docker or embedded)      │
│  Serving:    langgraph dev → React frontend             │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install dependencies

```bash
uv sync
npm install --prefix frontend
```

### 2. Download and convert OpenVINO models

The project uses 3 models, all converted to OpenVINO IR format via
[Optimum Intel](https://huggingface.co/docs/optimum/intel/index):

```bash
uv run convert-models
```

This runs `optimum-cli export openvino` for each model:

| Model | HuggingFace ID | Task | Format | Size |
| --- | --- | --- | --- | --- |
| **LLM** | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | text-generation-with-past | INT4 | ~700 MB |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | feature-extraction | FP32 | ~130 MB |
| **Reranker** | `BAAI/bge-reranker-v2-m3` | text-classification | FP32 | ~1.1 GB |

After conversion, the `models/` directory contains:

```text
models/
  tiny-llama-1b-chat/INT4_compressed_weights/
    openvino_model.xml + .bin, tokenizer files
  bge-small-en-v1.5/
    openvino_model.xml + .bin, tokenizer files
  bge-reranker-v2-m3/
    openvino_model.xml + .bin, tokenizer files
```

#### Using a different LLM

Convert any HuggingFace causal-LM to OpenVINO with:

```bash
optimum-cli export openvino \
  --model <hf-model-id> \
  --task text-generation-with-past \
  --weight-format int4 \
  ./models/<name>/INT4_compressed_weights
```

Examples:

```bash
# Phi-3-mini (3.8B, ~2.2 GB INT4)
optimum-cli export openvino --model microsoft/Phi-3-mini-4k-instruct \
  --task text-generation-with-past --weight-format int4 \
  ./models/phi-3-mini/INT4_compressed_weights

# Qwen2-1.5B (1.5B, ~1 GB INT4)
optimum-cli export openvino --model Qwen/Qwen2-1.5B-Instruct \
  --task text-generation-with-past --weight-format int4 \
  ./models/qwen2-1.5b/INT4_compressed_weights
```

Then set `LLM_MODEL_PATH` in `.env` to the new directory.

#### Using a different embedding model

```bash
optimum-cli export openvino --model BAAI/bge-base-en-v1.5 \
  --task feature-extraction \
  ./models/bge-base-en-v1.5
```

Then set `EMBEDDING_MODEL_PATH` in `.env`. Note: changing the embedding model
requires re-ingesting all documents (the vector dimensions may differ).

### 3. Start SeekDB

```bash
docker compose up -d        # wait ~60s on first run
```

Or use the embedded Python service (Linux only):

```python
import pylibseekdb
pylibseekdb.open_with_service("./seekdb-data", port=2881)
```

### 4. Configure environment

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_MODEL_PATH` | ./models/tiny-llama-1b-chat/INT4_compressed_weights | OpenVINO LLM directory |
| `EMBEDDING_MODEL_PATH` | ./models/bge-small-en-v1.5 | OpenVINO embedding model directory |
| `RERANK_MODEL_PATH` | ./models/bge-reranker-v2-m3 | OpenVINO reranker directory (remove to disable) |
| `OPENVINO_DEVICE` | CPU | Inference device: CPU, GPU, or NPU |
| `MAX_NEW_TOKENS` | 512 | Max tokens for LLM generation |
| `SEEKDB_HOST` | 127.0.0.1 | SeekDB host |
| `SEEKDB_PORT` | 2881 | SeekDB port |

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
embedded with the OpenVINO bge-small-en-v1.5 model (384-dim), and indexed
into OceanBase/SeekDB.

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

1. The **retrieve** node embeds the query, searches SeekDB, and reranks results.
2. The **generate** node feeds context + question to the local LLM.
3. The answer renders as markdown in the frontend.

## Hardware requirements

- **Minimum**: 8 GB RAM, x86_64 CPU with AVX2 (Intel 4th gen+, AMD Zen+)
- **Recommended**: 16 GB RAM, Intel Core Ultra / Xeon with AMX
- **GPU acceleration**: Set `OPENVINO_DEVICE=GPU` with Intel Arc / iGPU
- **NPU acceleration**: Set `OPENVINO_DEVICE=NPU` on Intel Core Ultra laptops

## How it works

The RAG pipeline flows through a LangGraph `StateGraph`:

1. **Embed query** — bge-small-en-v1.5 converts the question to a 384-dim vector
2. **Retrieve** — OceanBase/SeekDB returns top-k similar documents
3. **Rerank** — bge-reranker-v2-m3 cross-encoder re-scores and keeps top 3
4. **Generate** — TinyLlama (or your chosen LLM) produces an answer from context

All 3 models load once at startup via `openvino_genai` pipelines. No PyTorch
runtime is needed — only the OpenVINO inference engine.

## Why `openvino-genai` instead of `langchain-huggingface`?

LangChain's official OpenVINO integration uses `HuggingFacePipeline` with
`backend="openvino"` (see [docs](https://python.langchain.com/docs/integrations/llms/openvino)):

```python
# Official LangChain way (requires PyTorch + transformers + optimum-intel)
from langchain_huggingface import HuggingFacePipeline

ov_llm = HuggingFacePipeline.from_model_id(
    model_id="ov_model_dir",
    task="text-generation",
    backend="openvino",
    model_kwargs={"device": "CPU", "ov_config": ov_config},
)
```

This template uses `openvino-genai` (Intel's newer GenAI API) instead:

```python
# Our approach (no PyTorch at runtime)
import openvino_genai
pipe = openvino_genai.LLMPipeline("./model", "CPU")
```

| | `HuggingFacePipeline` (official) | `openvino_genai` (this template) |
| --- | --- | --- |
| Runtime deps | PyTorch + transformers + optimum | openvino + openvino-genai only |
| Install size | ~2 GB+ | ~200 MB |
| Embeddings | Not supported via this path | `TextEmbeddingPipeline` native |
| Reranking | Not supported | Compiled cross-encoder model |
| Streaming | HF pipeline `stream()` | `StreamerBase` protocol |

We chose `openvino-genai` because it provides native embedding and reranking
pipelines (not just LLM), avoids the ~2 GB PyTorch install, and matches the
patterns in Intel's [RAG notebook](https://github.com/openvinotoolkit/openvino_notebooks/tree/latest/notebooks/llm-rag-langchain).

To switch to the official approach, replace `ov_models.py` with:

```bash
pip install langchain-huggingface "optimum[openvino,nncf]"
```

```python
from langchain_huggingface import HuggingFacePipeline

llm = HuggingFacePipeline.from_model_id(
    model_id="./models/tiny-llama-1b-chat/INT4_compressed_weights",
    task="text-generation",
    backend="openvino",
    model_kwargs={"device": "CPU"},
    pipeline_kwargs={"max_new_tokens": 512},
)
```

Note: this adds PyTorch as a runtime dependency and loses native embedding/reranking support.
