# {{ cookiecutter.project_name }}

LangChain agentic RAG scaffolded with
`agentseek create langchain/agentic-rag`.

The backend serves a `create_agent(...)` graph through `langgraph dev`.
The frontend streams user messages, tool calls (retrieval), and the final
markdown answer.

## Setup

```bash
docker compose up -d        # start SeekDB (wait ~60s on first run)
uv sync
npm install --prefix frontend

cp .env.example .env
# Fill in backend secrets in .env:
# - Set AGENTSEEK_MODEL_PROVIDER and AGENTSEEK_MODEL
# - Fill only the matching provider block
# - If you switch providers, switch AGENTSEEK_MODEL to that provider's model id
# - Leave that provider's base URL empty to use the official endpoint
```

`agent.py` uses `AGENTSEEK_MODEL_PROVIDER` to choose a native LangChain
provider integration for OpenAI, Anthropic, or Gemini. Fill only that
provider's env block in `.env`; if its base URL is blank, the generated app
uses the provider's official default endpoint. You can also override the
scaffolded model name via `AGENTSEEK_MODEL` (or the compatibility alias
`BUB_MODEL`) without editing code. The template still defaults
`LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S=300` for the `openai` provider so
slow OpenAI-compatible tool-call streams do not die after LangChain OpenAI's
default gap timeout.

If you change `AGENTSEEK_MODEL_PROVIDER`, also change `AGENTSEEK_MODEL` to a
model served by that provider. The scaffold defaults to `openai` with
`{{ cookiecutter.default_model }}`, so pointing `OPENAI_API_BASE` at a
compatible gateway (e.g. SiliconFlow) works out of the box.

## Ingest

Before running the agent, ingest documents into the knowledge base:

```bash
# Web pages
uv run ingest https://lilianweng.github.io/posts/2023-06-23-agent/

# Local files or directories (.txt, .md)
uv run ingest ./docs/

# Multiple sources at once
uv run ingest ./notes/ https://example.com/article
```

Documents are split into 1000-character chunks with 200-character overlap,
embedded via `DefaultEmbeddingFunctionAdapter` from `langchain-oceanbase`
(384-dim, runs locally, no API key), and indexed into the configured SeekDB
table.

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
- The final assistant response renders as markdown with structured headings.

For complex queries, the agent performs multiple retrieval calls autonomously:

```text
Compare chain-of-thought prompting with tree-of-thought. How do adversarial attacks exploit these reasoning methods?
```

Expected: multiple "Tool: retrieve" cards appear (3–6 searches), followed by a
comprehensive cross-document synthesis.
