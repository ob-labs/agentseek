# {{ cookiecutter.project_name }}

A LangGraph CLI remote agent bridged into agentseek through
`agentseek-langchain.LangGraphClientRunnable`.

## Quickstart

```bash
uv sync --extra langchain
uv pip install -r requirements.txt

# Start the remote LangGraph dev server (separate terminal):
langgraph dev

# Bridge to agentseek:
export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.gateway_binding:build_spec
uv run --no-sync agentseek run "Plan the rollout."
```

Author: {{ cookiecutter.author }}
