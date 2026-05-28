# {{ cookiecutter.project_name }}

Pure DeepAgents research agent scaffolded with
`agentseek create deepagents/research`.

The backend serves a `create_deep_agent(...)` graph through `langgraph dev`.
The frontend streams user messages, tool calls, optional sub-agent delegation,
and the final markdown answer.

## Setup

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
cp frontend/.env.example frontend/.env
# Fill in either OPENAI_* or AGENTSEEK_* in .env, and set TAVILY_API_KEY.
```

`agent.py` bridges `AGENTSEEK_API_KEY` / `AGENTSEEK_API_BASE` into
`OPENAI_API_KEY` / `OPENAI_API_BASE` when only the former are set, so the
default `openai:...` model works against OpenAI-compatible gateways.
The template also defaults `LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S=300` so
slow tool-call streams from compatible gateways do not die after LangChain
OpenAI's 120s default gap timeout.

## Run

Start the backend:

```bash
uv run langgraph dev --port {{ cookiecutter.langgraph_port }} --no-browser
```

Start the frontend in a second terminal:

```bash
npm run --prefix frontend dev
```

By default the backend listens on
`http://127.0.0.1:{{ cookiecutter.langgraph_port }}` and the frontend on
`http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
Research what LangGraph 1.0 added vs 0.x. Cite sources.
```

Expected behavior:

- Tool cards appear for `tavily_search` and, when the model delegates,
  `task` as a "Sub-agent: research-agent" card.
- Each card expands while running, then collapses after its result lands.
- The final assistant response renders as markdown with linked citations.
