# {{ cookiecutter.project_name }}

LangChain agentic RAG scaffolded with
`agentseek create langchain/agentic-rag`.

The backend serves a `create_agent(...)` graph through `langgraph dev`.
The frontend streams user messages, tool calls (retrieval), and the final
markdown answer.

## Quickstart

```bash
cp .env.example .env
$EDITOR .env

uv sync
npm install --prefix frontend
docker compose up -d

agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek dev
```

Use `agentseek task --list` to see lifecycle helper tasks. The generated
project declares the development stack in `.agentseek/lifecycle.toml`.

## Environment

Set `AGENTSEEK_MODEL_PROVIDER` to `openai`, `anthropic`, or `google_genai`,
then set `AGENTSEEK_MODEL` to a model served by that provider. Fill only the
matching provider credential block:

```text
openai       -> OPENAI_API_KEY, optional OPENAI_API_BASE
anthropic    -> ANTHROPIC_API_KEY, optional ANTHROPIC_API_URL
google_genai -> GOOGLE_API_KEY, optional GOOGLE_API_BASE
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

The lifecycle spec checks `.env`, frontend dependencies, and the stable SeekDB
connection variables. Provider API keys are documented in `.env.example` but
are not lifecycle-required because lifecycle v1 does not support conditional
requirements by selected provider.

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

```bash
agentseek dev
```

By default the backend listens on `http://127.0.0.1:2024` and the frontend on
`http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

Run `agentseek doctor --live` after `agentseek dev` starts to check the
backend and frontend HTTP endpoints declared in the lifecycle spec.

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
