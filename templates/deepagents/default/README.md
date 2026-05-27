# DeepAgents — default template

Scaffolds a local `create_deep_agent(...)` runnable bound to AgentSeek through
`agentseek-langchain`. Mirrors the `examples/langchain_deepagents` example.

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
  .env.example
  src/{{ project_slug }}/
    __init__.py
    demo_binding.py
    settings.py
```
