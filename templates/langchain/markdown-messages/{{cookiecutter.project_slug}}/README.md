# {{ cookiecutter.project_name }}

A pure LangChain `create_agent` graph served by `langgraph dev`, with a Vite +
React frontend that streams messages and renders them as markdown.

## Setup

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
cp frontend/.env.example frontend/.env
# Fill in either OPENAI_* or AGENTSEEK_* in .env.
```

`src/{{ cookiecutter.project_slug }}/agent.py` contains the standard
`AGENTSEEK_*` to `OPENAI_*` env bridge, so OpenAI-compatible endpoints work
even when only the agentseek-style pair is set.

## Run

Start the backend:

```bash
uv run langgraph dev --port {{ cookiecutter.langgraph_port }} --no-browser
```

Start the frontend in another terminal:

```bash
npm run --prefix frontend dev
```

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Smoke test

Ask:

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
