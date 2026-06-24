# langchain/agentic-rag-openvino

Cookiecutter template for an **agentic RAG** application running fully local
with [OpenVINO](https://docs.openvino.ai/) via LangChain's official
[langchain-huggingface](https://python.langchain.com/docs/integrations/llms/openvino)
integration and [OceanBase/SeekDB](https://github.com/oceanbase/seekdb) as the
vector store. No cloud API keys required.

Uses the same `create_agent` + tool-calling pattern as `langchain/agentic-rag`,
just with local OpenVINO models instead of cloud APIs.

## How it integrates

```python
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace, HuggingFaceEmbeddings
from langchain.agents import create_agent

# LLM: HuggingFacePipeline with backend="openvino"
ov_llm = HuggingFacePipeline.from_model_id(
    model_id="./models/tiny-llama/INT4", task="text-generation",
    backend="openvino", model_kwargs={"device": "CPU"},
)
model = ChatHuggingFace(llm=ov_llm)  # has bind_tools → works with create_agent

# Embeddings: HuggingFaceEmbeddings with backend="openvino"
embeddings = HuggingFaceEmbeddings(
    model_name="./models/bge-small-en-v1.5",
    model_kwargs={"device": "cpu", "backend": "openvino"},
)

# Same agent pattern as cloud template
graph = create_agent(model=model, tools=[retrieve], system_prompt=PROMPT)
```

## What's generated

- **Backend** — a `create_agent` graph with a retrieval tool backed by
  `OceanbaseVectorStore`, served by `langgraph dev`. The agent autonomously
  decides when and how many times to search the knowledge base.
- **Frontend** — React + Vite chat UI with streaming tool-call cards and
  markdown rendering via `@langchain/react` `useStream`.
- **Ingest CLI** — `uv run ingest` loads documents, embeds with OpenVINO, and
  indexes into SeekDB.
- **Model converter** — `uv run convert-models` downloads HuggingFace models
  and exports them to OpenVINO IR with INT4/INT8 weight compression.

## Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** with npm (for the Vite frontend)
- **Linux x86_64** (primary) or macOS x86_64 (via Rosetta)
- **8+ GB RAM** (16 GB recommended for larger models)
- **Docker** (for SeekDB)

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
agentseek task seekdb        # start SeekDB in the background
agentseek task ingest-sample
agentseek dev                # SeekDB + backend + frontend
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
| `seekdb_db_name` | test | SeekDB database name |
| `vector_table_name` | rag_documents | Vector store table name |
| `frontend_port` | 5174 | Frontend Vite dev server port |

## Design decisions

- **Official LangChain integration**: uses `langchain-huggingface` with
  `backend="openvino"` for both LLM and embeddings — standard, maintained,
  documented.
- **`ChatHuggingFace` enables `create_agent`**: wrapping the pipeline as a
  chat model gives `bind_tools()` support, so the agent can autonomously
  decide when to search (same as cloud template).
- **`optimum-cli export openvino`** for model conversion: standard HuggingFace
  tooling, supports INT4/INT8/FP16 weight compression.
- **OceanBase/SeekDB** for vector storage: same production-grade DB as the
  cloud template.
- **INT4 for LLM, FP32 for embeddings**: LLM benefits most from compression;
  embedding quality degrades with quantization.
- **Supports CPU, GPU, NPU** via `OPENVINO_DEVICE` env var.
- **PyTorch in the venv** (via `optimum[openvino]`) is used only for model
  conversion (`convert-models`). At runtime, `langchain-huggingface` uses
  optimum-intel which does import torch. The generated README documents an
  alternative `openvino-genai` path that avoids torch at runtime and adds
  native reranking — see "Advanced" section.
