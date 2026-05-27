# {{ cookiecutter.project_name }}

A DeepAgents-based agent project, scaffolded with `agentseek create deepagents`.

The binding export is:

```text
{{ cookiecutter.project_slug }}.demo_binding:build_spec
```

## Quickstart

```bash
uv sync --extra langchain
uv pip install -r requirements.txt

cp .env.example .env
# fill in AGENTSEEK_MODEL / AGENTSEEK_API_KEY / AGENTSEEK_API_BASE

export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC={{ cookiecutter.project_slug }}.demo_binding:build_spec

uv run --no-sync --no-env-file agentseek run "Plan a rollback-safe migration." \
  --session-id {{ cookiecutter.project_slug }}-demo
```

## Files

| File | Purpose |
| --- | --- |
| `src/{{ cookiecutter.project_slug }}/demo_binding.py` | Builds the DeepAgents runnable and exports `build_spec()`. |
| `src/{{ cookiecutter.project_slug }}/settings.py` | Reads env vars; bridges `AGENTSEEK_*` into `OPENAI_*` when needed. |
| `requirements.txt` | Extra Python dependencies. |

Author: {{ cookiecutter.author }}
