# {{ cookiecutter.project_name }}

A lightweight Bub AG-UI agent project with an AgentSeek lifecycle spec.

## Quickstart

```bash
cp .env.example .env
$EDITOR .env
uv sync
npm install --prefix frontend

uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
uvx agentseek task --list
```

The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`,
the CopilotKit runtime to `http://127.0.0.1:{{ cookiecutter.copilotkit_port }}/api/copilotkit`,
and the Bub AG-UI gateway to `http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent`.

The generated runtime depends on `bub==0.3.9` plus the AG-UI Bub channel plugin.
AgentSeek is only used as an external template and lifecycle tool. This project
declares lifecycle behavior in `.agentseek/lifecycle.toml`.

`.env` is the readiness and lifecycle env source for `agentseek doctor`. It is
not injected into child processes by AgentSeek. The Bub gateway and AG-UI
channel read the project `.env` themselves, while the frontend uses
`frontend/.env` or shell environment variables for Vite and CopilotKit runtime
settings. For containers or process managers, pass runtime environment variables
through that runtime.

Author: {{ cookiecutter.author }}
