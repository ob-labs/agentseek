# {{ cookiecutter.project_name }}

Pure DeepAgents research agent scaffolded with
`agentseek new deepagents/research`.

The backend serves a `create_deep_agent(...)` graph through `langgraph dev`.
The frontend streams user messages, tool calls, optional sub-agent delegation,
and the final markdown answer.

## Setup

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
cp frontend/.env.example frontend/.env
# Fill in backend secrets in .env:
# - Set AGENTSEEK_MODEL_PROVIDER and AGENTSEEK_MODEL
# - Fill only the matching provider block
# - If you switch providers, switch AGENTSEEK_MODEL to that provider's model id
# - Leave that provider's base URL empty to use the official endpoint
# - Set TAVILY_API_KEY
# frontend/.env only needs changes if you want a non-default LangGraph URL.
```

`agent.py` uses `AGENTSEEK_MODEL_PROVIDER` to choose a native LangChain
provider integration for OpenAI, Anthropic, or Gemini. Fill only that
provider's env block in `.env`; if its base URL is blank, the generated app
uses the provider's official default endpoint. You can also override the
scaffolded model name via `AGENTSEEK_MODEL` (or the compatibility aliases
`DEEPAGENTS_MODEL` / `BUB_MODEL`) without editing code. The template still
defaults `LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S=300` for the `openai`
provider so slow OpenAI-compatible tool-call streams do not die after
LangChain OpenAI's default gap timeout.

If you change `AGENTSEEK_MODEL_PROVIDER`, also change `AGENTSEEK_MODEL` to a
model served by that provider. The scaffold defaults to `openai` with
`gpt-4.1-mini`, so leaving `OPENAI_API_BASE` blank targets the official OpenAI
endpoint out of the box.

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

- A live **Research plan** todo panel appears when the agent writes todos.
- Tool cards appear for `tavily_search` and, when the model delegates,
  `task` as a "Sub-agent: research-agent" card.
- Each card expands while running, then collapses after its result lands.
- The final assistant response renders as markdown with linked citations.
