# DeepAgents — default template

Scaffolds a local `create_deep_agent(...)` runnable bound to AgentSeek through
`agentseek-langchain`.

## Architecture

```text
uv run agentseek run / agentseek gateway
  -> agentseek-langchain
    -> messages_spec(...)
      -> create_deep_agent(...)
```

The binding export is `{{ project_slug }}.demo_binding:build_spec`.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL` value used by `settings.py`. |

## Generated layout

```
{{ project_slug }}/
  README.md
  pyproject.toml
  requirements.txt
  Dockerfile
  .env.example
  src/{{ project_slug }}/
    __init__.py
    demo_binding.py
    settings.py
```

## Key code patterns

The core binding is two layers — build the DeepAgents runnable, then wrap it
with `messages_spec`:

```python
from agentseek_langchain import messages_spec
from deepagents import create_deep_agent

def build_agent():
    return create_deep_agent(
        model=settings.require_model(),
        tools=[outline_answer],
        system_prompt="You are a pragmatic engineering assistant.",
    )

def build_spec():
    return messages_spec(build_agent(), include_agents_md=True)
```
