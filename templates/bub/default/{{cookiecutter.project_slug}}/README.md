# {{ cookiecutter.project_name }}

A lightweight Bub agent project. Runs an AG-UI gateway plus a CopilotKit
frontend, no LangChain layer.

## Quickstart

```bash
# Start the gateway
uv sync --extra ag-ui
export AGENTSEEK_STREAM_OUTPUT=true
uv run agentseek gateway --enable-channel ag-ui

# Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`,
the gateway to `http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent`.

Author: {{ cookiecutter.author }}
