# {{ cookiecutter.project_name }}

A Bub agent project with ContextSeek semantic memory and an AgentSeek
lifecycle spec. Runs a Bub AG-UI gateway, a ctx HTTP API server, and a
CopilotKit frontend.

## Setup

```bash
cp .env.example .env
$EDITOR .env

uvx agentseek info
uvx agentseek task sync
uvx agentseek task frontend
uvx agentseek doctor
```

## Run

```bash
uvx agentseek dev
```

`agentseek dev` starts the long-running processes declared in
`.agentseek/lifecycle.toml`:

| Process | Default port | Description |
| --- | --- | --- |
| `uv run bub gateway --enable-channel ag-ui` | {{ cookiecutter.gateway_port }} | Bub AG-UI `/agent` endpoint |
| `uv run ctx-server` | {{ cookiecutter.ctx_server_port }} | `/ctx/add`, `/ctx/overview`, `/ctx/retrieve` |
| `npm run dev` | {{ cookiecutter.frontend_port }} / {{ cookiecutter.copilotkit_port }} | Vite + React chat UI and Copilot Runtime |

Run `uvx agentseek task --list` to inspect project tasks. To pre-load example
ContextSeek entries, run:

```bash
uvx agentseek task seed
```

## Runtime environment ownership

`.env` is the readiness and env source for `agentseek info` and
`agentseek doctor`. Lifecycle v1 does not inject `.env` into child processes.
Runtime environment is owned by the launched processes and the caller's shell:
the Bub AG-UI channel and ctx server read `.env` themselves, Vite reads
`frontend/.env`, and shell variables override file values where the underlying
tools support that behavior.

## Smoke test

```bash
# Add a piece of knowledge
curl -s -X POST http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/add \
  -H "Content-Type: application/json" \
  -d '{"content": "The capital of France is Paris.", "scope": "facts"}'

# Retrieve it
curl -s -X POST http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "France capital", "scope": "facts"}'

# Inspect all stored entries
curl -s "http://127.0.0.1:{{ cookiecutter.ctx_server_port }}/ctx/overview?scope=facts"
```

## ContextSeek dependency

`agentseek-contextseek` is resolved from the same source as AgentSeek templates:
{% if cookiecutter._agentseek_source_path %}
- **Local editable install** from `{{ cookiecutter._agentseek_source_path }}/contrib/agentseek-contextseek`
{% else %}
- **Git source** at `{{ cookiecutter._agentseek_source_url }}` (subdirectory `contrib/agentseek-contextseek`)
{% endif %}

Author: {{ cookiecutter.author }}
