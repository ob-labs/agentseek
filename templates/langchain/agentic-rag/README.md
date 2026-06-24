# langchain/agentic-rag

Cookiecutter template for an **agentic RAG** application using
[LangChain](https://docs.langchain.com/oss/langchain) with an
[OceanBase/SeekDB](https://github.com/oceanbase/seekdb) vector store and
seekdb embed (384-dim, no API key required).

The generated project includes:

- **Backend** — a `create_agent` graph with a retrieval tool backed by
  `OceanbaseVectorStore`, served by `langgraph dev`. The agent autonomously
  decides when and how many times to search the knowledge base.
- **Frontend** — React + Vite chat UI with streaming tool-call cards and
  markdown rendering via `@langchain/react` `useStream`.
- **Ingest CLI** — `uv run ingest` loads documents from files, directories,
  or URLs, chunks them, and indexes into SeekDB.
- **AgentSeek lifecycle** — `.agentseek/lifecycle.toml` declares
  `agentseek info`, `agentseek doctor`, `agentseek dev`, and helper tasks.

## Prerequisites

This template requires **Python 3.12+** and uses [uv](https://docs.astral.sh/uv/)
for dependency management. Install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You also need a running SeekDB instance. The generated project includes a
`docker-compose.yml` that starts one, or you can use the embedded
`pylibseekdb` launcher on Linux.

## Quick start

```bash
# 1. Scaffold
uv tool install agentseek                       # install the agentseek CLI once
agentseek create langchain/agentic-rag          # scaffold the project

# 2. Project setup
cd <project_slug>
cp .env.example .env        # fill in API keys
uv sync
npm install --prefix frontend
docker compose up -d        # start SeekDB
agentseek doctor
agentseek dev --dry-run

# 3. Run
agentseek dev
```

## Cookiecutter variables

| Variable | Default | Description |
| --- | --- | --- |
| `project_name` | My RAG Agent | Human-readable project name |
| `project_slug` | *(derived)* | Python package / directory name |
| `author` | Your Name | Author for pyproject.toml |
| `default_model_provider` | openai | openai / anthropic / google_genai |
| `default_model` | openai:Pro/zai-org/GLM-5.1 | Model ID for the chosen provider |
| `seekdb_path` | ./.seekdb-data | Local data path (Docker volume mount) |
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
  .agentseek/lifecycle.toml
  .env.example
  src/{{ project_slug }}/
    __init__.py
    agent.py
    ingest.py
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

- Uses provider-first runtime config: generated apps select `openai`,
  `anthropic`, or `google_genai` in `.env`, then fill only the matching
  credential block.
- Treats blank provider base URLs as "use the official endpoint", while still
  allowing custom compatible gateways per provider (e.g. SiliconFlow).
- Lets generated apps override the scaffold-time model via `AGENTSEEK_MODEL`
  (plus `BUB_MODEL` compatibility alias) in `.env`.
- Defaults to provider `openai` with model `Pro/zai-org/GLM-5.1` targeting
  SiliconFlow; swap to `gpt-4.1-mini` and clear `OPENAI_API_BASE` for direct
  OpenAI use.
- Uses `langchain-oceanbase[pyseekdb]` for both the vector store client and
  the built-in embedding function (`DefaultEmbeddingFunctionAdapter`, 384-dim).
- The agent pattern (`create_agent` + tool) allows the LLM to perform
  multi-step retrieval — complex queries trigger multiple searches
  autonomously, unlike a fixed two-step RAG chain.
- LangSmith tracing is opt-in via `LANGSMITH_TRACING=true` in `.env`.
