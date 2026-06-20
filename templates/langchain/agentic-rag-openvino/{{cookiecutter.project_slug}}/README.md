# {{ cookiecutter.project_name }}

LangChain agentic RAG running **fully local** with
[OpenVINO](https://docs.openvino.ai/) via the official
[langchain-huggingface](https://python.langchain.com/docs/integrations/llms/openvino)
integration and [OceanBase/SeekDB](https://github.com/oceanbase/seekdb)
as the vector store. No cloud API keys required.

Scaffolded with `agentseek create langchain/agentic-rag-openvino`.

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  All inference local via langchain-huggingface + OpenVINO │
├──────────────────────────────────────────────────────────┤
│  LLM:        HuggingFacePipeline(backend="openvino")     │
│              → ChatHuggingFace → create_agent             │
│  Embedding:  HuggingFaceEmbeddings(backend="openvino")   │
│  Vector DB:  OceanBase/SeekDB                            │
│  Serving:    langgraph dev → React frontend              │
└──────────────────────────────────────────────────────────┘
```

The agent uses `create_agent` with tool-calling — same pattern as the
cloud-based `agentic-rag` template. The LLM decides when and how many
times to search the knowledge base.

## Setup

### 1. Install dependencies

```bash
uv sync
npm install --prefix frontend
```

### 2. Download and convert OpenVINO models

```bash
uv run convert-models
```

This downloads and converts via `optimum-cli export openvino`:

| Model | HuggingFace ID | Task | Format | Size |
| --- | --- | --- | --- | --- |
| **LLM** | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | text-generation-with-past | INT4 | ~700 MB |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | feature-extraction | FP32 | ~130 MB |

#### Using a different LLM

```bash
optimum-cli export openvino \
  --model microsoft/Phi-3-mini-4k-instruct \
  --task text-generation-with-past \
  --weight-format int4 \
  ./models/phi-3-mini/INT4_compressed_weights
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

Key variables:

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_MODEL_PATH` | ./models/tiny-llama-1b-chat/INT4_compressed_weights | OpenVINO LLM directory |
| `EMBEDDING_MODEL_PATH` | ./models/bge-small-en-v1.5 | OpenVINO embedding model directory |
| `OPENVINO_DEVICE` | CPU | Inference device: CPU, GPU, or NPU |
| `MAX_NEW_TOKENS` | 512 | Max tokens for LLM generation |
| `SEEKDB_HOST` | 127.0.0.1 | SeekDB host |
| `SEEKDB_PORT` | 2881 | SeekDB port |

## Ingest

```bash
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/
uv run ingest ./docs/
```

Documents are chunked (1000 chars, 200 overlap), embedded with
`HuggingFaceEmbeddings(backend="openvino")` using bge-small-en-v1.5
(384-dim), and indexed into SeekDB.

## Run

```bash
uv run langgraph dev --no-browser    # backend :2024
npm run --prefix frontend dev        # frontend :{{ cookiecutter.frontend_port }}
```

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
What is task decomposition?
```

The agent autonomously calls the `retrieve` tool, then generates a
grounded answer — same behavior as the cloud-based template.

## How it works

The integration uses LangChain's official OpenVINO path:

```python
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace

# Load LLM with OpenVINO backend (no PyTorch inference, just optimum-intel)
ov_llm = HuggingFacePipeline.from_model_id(
    model_id="./models/tiny-llama-1b-chat/INT4_compressed_weights",
    task="text-generation",
    backend="openvino",
    model_kwargs={"device": "CPU"},
)
# Wrap as ChatModel with bind_tools support
model = ChatHuggingFace(llm=ov_llm)

# Same create_agent pattern as cloud-based template
graph = create_agent(model=model, tools=[retrieve], system_prompt=...)
```

`ChatHuggingFace` provides `bind_tools()`, enabling the standard
`create_agent` flow where the LLM decides when to call retrieval tools.

## Hardware requirements

- **Minimum**: 8 GB RAM, x86_64 CPU with AVX2 (Intel 4th gen+, AMD Zen+)
- **Recommended**: 16 GB RAM, Intel Core Ultra / Xeon with AMX
- **GPU acceleration**: Set `OPENVINO_DEVICE=GPU` with Intel Arc / iGPU
- **NPU acceleration**: Set `OPENVINO_DEVICE=NPU` on Intel Core Ultra laptops
