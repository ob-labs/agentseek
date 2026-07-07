# {{ cookiecutter.project_name }}

A DeepAgents-based agent project, scaffolded with `agentseek create deepagents`.

The binding export is:

```text
{{ cookiecutter.project_slug }}.demo_binding:build_spec
```

## Quickstart

```bash
cp .env.example .env
$EDITOR .env

uvx agentseek info
uvx agentseek doctor
uvx agentseek task --list
uvx agentseek task sync

uvx agentseek dev
```

The gateway is declared in `.agentseek/lifecycle.toml` and defaults to
`http://127.0.0.1:{{ cookiecutter._gateway_port }}/agent`. AgentSeek is used as
the external lifecycle tool; the generated runtime is the project dependency
set in `pyproject.toml`.

## Environment

Copy `.env.example` to `.env` before running lifecycle checks. The generated
settings read `BUB_MODEL`, `BUB_API_KEY`, and optional `BUB_API_BASE`, with
`AGENTSEEK_*` and OpenAI-compatible aliases accepted where noted in the file.
`BUB_LANGCHAIN_SPEC` points the gateway at this package's `build_spec()`, and
`BUB_AG_UI_PORT` must match the service URLs declared in the lifecycle spec.

## Files

| File | Purpose |
| --- | --- |
| `.agentseek/lifecycle.toml` | Declares AgentSeek `info`, `doctor`, `dev`, and `task` behavior. |
| `.env.example` | Documents runtime model, provider, LangChain binding, and AG-UI port variables. |
| `src/{{ cookiecutter.project_slug }}/demo_binding.py` | Builds the DeepAgents runnable and exports `build_spec()`. |
| `src/{{ cookiecutter.project_slug }}/settings.py` | Reads env vars; bridges `AGENTSEEK_*` into `OPENAI_*` when needed. |
| `requirements.txt` | Extra Python dependencies. |

Author: {{ cookiecutter.author }}
