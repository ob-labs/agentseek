# {{ cookiecutter.project_name }}

A LangChain `create_agent` project with CopilotKit middleware, bound to
agentseek through `agentseek-langchain`.

## Quickstart

```bash
uv sync --extra ag-ui --extra langchain
uv pip install -r requirements.txt

cp .env.example .env
export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.demo_binding:build_spec

uv run --no-sync --no-env-file agentseek gateway --enable-channel ag-ui
```

Author: {{ cookiecutter.author }}
