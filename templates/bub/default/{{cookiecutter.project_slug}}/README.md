# {{ cookiecutter.project_name }}

A lightweight Bub AG-UI agent project with an AgentSeek lifecycle file.

## Quickstart

```bash
cp .env.example .env
uv sync
npm install --prefix frontend

uvx agentseek doctor
uvx agentseek dev
uvx agentseek task --list
```

The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`,
the CopilotKit runtime to `http://127.0.0.1:{{ cookiecutter.copilotkit_port }}/api/copilotkit`,
and the Bub AG-UI gateway to `http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent`.

The generated runtime depends on `bub==0.3.9` plus the AG-UI Bub channel plugin.
AgentSeek is only used as an external template and lifecycle tool; `duty` is
kept in the dev dependency group for direct local task-runner usage.

Author: {{ cookiecutter.author }}
