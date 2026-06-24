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

## Lifecycle commands

This project includes `.agentseek/lifecycle.toml`, so AgentSeek can inspect,
check, and run the local development stack:

```bash
agentseek info           # show services, environment, and lifecycle metadata
agentseek doctor         # run static checks for tools, paths, and .env
agentseek dev --dry-run  # print the SeekDB/backend/frontend startup plan
agentseek task --list    # list setup and data tasks
```

`agentseek doctor` intentionally does not download or convert OpenVINO models.
Use `agentseek task models` for that heavier step.

## Setup

> **Python 3.10+ required** (not 3.12+). OpenVINO runtime and
> `optimum[openvino]` have limited Python 3.13+ support, so this template
> uses `requires-python = ">=3.10"`.
>
> **Node.js 20+ recommended** for the Vite frontend dependencies.

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if you changed model paths, want a different OpenVINO device, or
want to enable LangSmith tracing. AgentSeek reads `.env` for lifecycle checks;
LangGraph, the ingest CLI, and Docker Compose also read it at runtime.

### 2. Install dependencies

```bash
uv sync
agentseek task frontend
agentseek doctor
```

`agentseek doctor` checks local prerequisites and does not run model conversion,
ingestion, or Docker startup.

### 3. Download and convert OpenVINO models

```bash
agentseek task models
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

### 4. Start SeekDB

```bash
agentseek task seekdb        # wait ~60s on first run
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
agentseek task ingest-sample
uv run ingest ./docs/
```

Documents are chunked (1000 chars, 200 overlap), embedded with
`HuggingFaceEmbeddings(backend="openvino")` using bge-small-en-v1.5
(384-dim), and indexed into SeekDB.

## Run

```bash
agentseek dev --dry-run
agentseek dev
```

`agentseek dev` starts SeekDB, `langgraph dev`, and the Vite frontend from the
lifecycle spec. In another terminal, use `agentseek doctor --live` to check the
declared HTTP endpoints.

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

## Advanced: native `openvino-genai` approach (with reranking)

The official `langchain-huggingface` path covers LLM and embeddings. For
**cross-encoder reranking**, you can use Intel's lower-level `openvino-genai`
package directly. This avoids `langchain-huggingface` entirely and provides
native `TextEmbeddingPipeline` + `TextRerankPipeline` + `LLMPipeline`:

```bash
pip install openvino-genai
optimum-cli export openvino --model BAAI/bge-reranker-v2-m3 \
  --task text-classification ./models/bge-reranker-v2-m3
```

```python
import openvino_genai

# Native embedding pipeline
emb_pipe = openvino_genai.TextEmbeddingPipeline("./models/bge-small-en-v1.5", "CPU")
vec = emb_pipe.embed_query("hello")  # 384-dim

# Native LLM pipeline
llm_pipe = openvino_genai.LLMPipeline("./models/tiny-llama/INT4", "CPU")
answer = llm_pipe.generate("What is RAG?", config)

# Native reranker (cross-encoder)
import openvino as ov
core = ov.Core()
reranker = core.compile_model("./models/bge-reranker-v2-m3/openvino_model.xml", "CPU")
tokenizer = openvino_genai.Tokenizer("./models/bge-reranker-v2-m3")
```

Trade-offs vs the `langchain-huggingface` approach:

| | `langchain-huggingface` (default) | `openvino-genai` (native) |
| --- | --- | --- |
| LangChain integration | Official, `bind_tools` works | Custom wrappers needed |
| Reranking | Not supported | Native pipeline |
| Runtime PyTorch | Yes (optimum-intel loads via torch) | No (pure C++ inference) |
| `create_agent` compatible | Yes | No (`LLM` base, no `bind_tools`) |

**Note on PyTorch**: both approaches need `optimum-cli` for initial model
conversion, which pulls in PyTorch. The difference is at **inference runtime**:
`langchain-huggingface` uses `optimum-intel` internally (which imports torch),
while `openvino-genai` is a pure C++ inference engine with only a thin Python
binding — no torch imported at runtime. In practice, since `optimum[openvino]`
is in `pyproject.toml` for `convert-models`, PyTorch ends up installed in both
cases. The benefit of `openvino-genai` is smaller runtime memory footprint
(torch not loaded into process) and native reranking support.

Use `openvino-genai` when you need reranking or want lower runtime memory.
Use `langchain-huggingface` (this template's default) when you want standard
LangChain tool-calling and `create_agent` compatibility.

## Hardware requirements

- **Minimum**: 8 GB RAM, x86_64 CPU with AVX2 (Intel 4th gen+, AMD Zen+)
- **Recommended**: 16 GB RAM, Intel Core Ultra / Xeon with AMX
- **GPU acceleration**: Set `OPENVINO_DEVICE=GPU` with Intel Arc / iGPU
- **NPU acceleration**: Set `OPENVINO_DEVICE=NPU` on Intel Core Ultra laptops
