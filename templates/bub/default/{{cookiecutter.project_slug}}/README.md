# {{ cookiecutter.project_name }}

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

The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`,
the CopilotKit runtime to `http://127.0.0.1:{{ cookiecutter.copilotkit_port }}/api/copilotkit`,
and the gateway to `http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent`.

Author: {{ cookiecutter.author }}
