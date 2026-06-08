# LangChain — cli-remote template

Scaffolds a project that runs a graph via `langgraph dev` and bridges it
into agentseek through `LangGraphClientRunnable`.

## Architecture

```text
uv run agentseek run / agentseek gateway
  -> agentseek-langchain
    -> LangGraphClientRunnable
      -> langgraph_sdk client
        -> uv run langgraph dev
          -> create_agent(...)
```

The bridge sends a messages-only state dict to the remote graph:

```python
{"messages": [...]}
```

This keeps local Bub runtime objects such as `mcp` out of the JSON request
while still matching the input shape expected by the remote `create_agent(...)`.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `langgraph_url` | Default LangGraph Agent Server URL. |
| `assistant_id` | Graph / assistant id (matches `langgraph.json`). |

## Generated layout

```
{{ project_slug }}/
  README.md
  pyproject.toml
  requirements.txt
  .env.example
  Dockerfile
  langgraph.json
  src/{{ project_slug }}/
    __init__.py
    remote_graph.py
    gateway_binding.py
    settings.py
```

## Key code patterns

The binding builds a `RunnableSpec` with a custom input adapter that
extracts only messages from the Bub state:

```python
from agentseek_langchain import LangGraphClientRunnable, RunnableSpec

def build_spec():
    runnable = LangGraphClientRunnable(client, assistant_id="agent")
    return RunnableSpec(
        runnable=runnable,
        build_input=_build_remote_input,
        parse_output=parse_messages_output,
        build_config=default_runnable_config,
    )
```
