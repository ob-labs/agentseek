# {{ cookiecutter.project_name }}

A Bub agent project with ContextSeek semantic memory. Runs an AG-UI
gateway, a ctx HTTP API server, and a CopilotKit frontend.

## Setup

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
# Fill in AGENTSEEK_API_KEY (and optionally AGENTSEEK_API_BASE).
```

## Run

```bash
uv run serve
```

This starts three processes simultaneously:

| Process | Default port | Description |
| --- | --- | --- |
| agentseek gateway | {{ cookiecutter.gateway_port }} | AG-UI `/agent` endpoint |
| ctx FastAPI server | {{ cookiecutter.ctx_server_port }} | `/ctx/add`, `/ctx/overview`, `/ctx/retrieve` |
| CopilotKit frontend | {{ cookiecutter.frontend_port }} | Vite + React chat UI |

On first boot, `seed.py` pre-loads a few example entries into the ContextSeek
store so the agent has something to retrieve immediately.

## Smoke test

```bash
# Add a piece of knowledge
curl -s -X POST http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/add \
  -H "Content-Type: application/json" \
  -d '{"content": "The capital of France is Paris.", "scope": "facts"}'

# Retrieve it
curl -s "http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/retrieve?query=France+capital&scope=facts"

# Inspect all stored entries
curl -s "http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/overview"
```

## ContextSeek dependency

`agentseek-contextseek` is resolved from the same source as `agentseek`:
{% if cookiecutter._agentseek_source_path %}
- **Local editable install** from `{{ cookiecutter._agentseek_source_path }}/contrib/agentseek-contextseek`
{% else %}
- **Git source** at `{{ cookiecutter._agentseek_source_url }}` (subdirectory `contrib/agentseek-contextseek`)
{% endif %}

Author: {{ cookiecutter.author }}
