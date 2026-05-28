# My Bub Agent

A lightweight Bub agent project. Runs an AG-UI gateway plus a CopilotKit
frontend, no LangChain layer.

## Quickstart

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
# Optionally merge in the model credentials from your existing repository root `.env`.

uv run agentseek run --no-browser
```

The frontend defaults to `http://127.0.0.1:5173`,
the CopilotKit runtime to `http://127.0.0.1:4000/api/copilotkit`,
and the gateway to `http://127.0.0.1:8088/agent`.

Author: Your Name
