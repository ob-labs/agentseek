# {{ cookiecutter.project_name }}

A pure LangChain `create_agent` graph served by `langgraph dev`, with a Vite +
React frontend that streams messages and renders them as markdown. The project
declares its local lifecycle in `.agentseek/lifecycle.toml`.

## Setup

```bash
cp .env.example .env
$EDITOR .env

uv sync
npm install --prefix frontend

agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek task --list
```

`src/{{ cookiecutter.project_slug }}/agent.py` contains the standard
`AGENTSEEK_*` to `OPENAI_*` env bridge, so OpenAI-compatible endpoints work
even when only the agentseek-style pair is set. Fill exactly one credential
pair in `.env`:

- `AGENTSEEK_API_KEY` and optional `AGENTSEEK_API_BASE`
- `OPENAI_API_KEY` and optional `OPENAI_API_BASE`

Set `AGENTSEEK_MODEL` or `OPENAI_MODEL` to a chat model exposed by your
provider. If neither is set, the agent falls back to
`{{ cookiecutter.default_model }}`.

The lifecycle spec reads `.env` only for declared environment requirements. It
does not inject `.env` values into child processes; `langgraph.json` loads
`.env` for the backend.

The frontend works with its scaffolded defaults. Copy `frontend/.env.example`
to `frontend/.env` only if you need to override `VITE_LANGGRAPH_API_URL` or
`FRONTEND_PORT`.

## Run

Start both backend and frontend through AgentSeek:

```bash
agentseek dev
```

By default the backend listens on `http://127.0.0.1:{{ cookiecutter.langgraph_port }}`
and the frontend on `http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

Development entrypoints, services, tasks, and live readiness probes are defined
in `.agentseek/lifecycle.toml`.

You can still run the underlying commands manually when debugging:

```bash
uv run langgraph dev --port {{ cookiecutter.langgraph_port }} --no-browser
npm run --prefix frontend dev
```

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
show me a table of three colors with hex codes
```

Expected behavior:

- the human message appears in the chat
- the assistant response renders through markdown, including a real HTML table
- fenced code blocks and lists also render correctly on later turns

## Notes

- The frontend intentionally pins `@langchain/react` to `~0.3.5`. Newer 1.x
  clients call endpoints that the bundled `langgraph-cli[inmem]` server line
  does not expose yet.
