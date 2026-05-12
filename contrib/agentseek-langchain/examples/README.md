# LangChain Examples

These are repository examples for `agentseek-langchain`.

Each example is a plain Python file under `examples/`. To load one directly, add this directory to `PYTHONPATH` and point `AGENTSEEK_LANGCHAIN_FACTORY` at `<module>:<factory>`.

## At A Glance

| Example | Factory | Purpose |
| --- | --- | --- |
| `minimal_runnable.py` | `minimal_runnable:minimal_lc_agent` | Minimal local `RunnableBinding` example. |
| `deepagents_dashscope.py` | `deepagents_dashscope:dashscope_deep_agent` | DeepAgents example using DashScope-compatible settings. |
| `remote_agent_protocol.py` | `remote_agent_protocol:remote_agent_protocol_agent` | Adapter around a user-managed remote agent-protocol service. |

## Prerequisites

From the repo root:

```bash
uv sync --all-packages
```

For the DashScope DeepAgents example, install repository development dependencies if they are not already present:

```bash
uv sync --all-packages --group dev
```

## Configure

All examples follow the same factory contract:

- the factory accepts `request: LangchainFactoryRequest`
- the factory returns `RunnableBinding`
- the factory is referenced as `<module>:<factory>`

Expose this directory before using the examples directly:

```bash
export PYTHONPATH="$(pwd)/contrib/agentseek-langchain/examples${PYTHONPATH:+:$PYTHONPATH}"
```

## Run

### Minimal Runnable

Factory path:

```bash
minimal_runnable:minimal_lc_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=minimal_runnable:minimal_lc_agent
```

Run it:

```bash
uv run agentseek chat
uv run agentseek run "Summarize this workspace in one sentence."
```

### DeepAgents + DashScope

Factory path:

```bash
deepagents_dashscope:dashscope_deep_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=deepagents_dashscope:dashscope_deep_agent
export AGENTSEEK_MODEL=openai:glm-5.1
export AGENTSEEK_API_KEY=your-dashscope-api-key
export AGENTSEEK_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

Optional explicit overrides for the example:

```bash
export AGENTSEEK_DEEPAGENTS_MODEL=glm-5.1
export AGENTSEEK_DEEPAGENTS_API_KEY=your-dashscope-api-key
export AGENTSEEK_DEEPAGENTS_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

Run it:

```bash
uv run agentseek chat
uv run agentseek gateway --enable-channel marimo
```

This example includes:

```python
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"
```

If `AGENTSEEK_LANGCHAIN_INCLUDE_BUB_TOOLS=true`, the DeepAgents example also appends Bub-bridged tools to its tool list.
This is only an example factory. The DeepAgents runtime remains user-managed.

### Remote Agent Protocol

Factory path:

```bash
remote_agent_protocol:remote_agent_protocol_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_FACTORY=remote_agent_protocol:remote_agent_protocol_agent
export AGENTSEEK_AGENT_PROTOCOL_URL=http://localhost:2024
export AGENTSEEK_AGENT_PROTOCOL_AGENT_ID=agent
```

Optional override:

```bash
export AGENTSEEK_AGENT_PROTOCOL_API_KEY=your-api-key
export AGENTSEEK_AGENT_PROTOCOL_STATEFUL=true
```

Run it:

```bash
uv run agentseek chat
uv run agentseek run "Summarize this workspace in one sentence."
```

Notes:

- `AGENTSEEK_AGENT_PROTOCOL_STATEFUL=true` maps each Bub session to a deterministic protocol `thread_id`.
- The adapter uses `langgraph_sdk.get_client()` as transport, but only relies on the standard `agent_id`, `thread_id`, `messages`, `values`, and `stream_mode` subset.
- Remote tool execution remains owned by the server-side assistant; local Bub tools are not forwarded into the remote runtime.
- This is an example factory around a user-managed remote runnable, not a separate plugin mode.

## Verify

From the repository root:

```bash
uv sync --all-packages --group dev
uv run python -m pytest contrib/agentseek-langchain/tests/test_examples.py
```

## Limitations

- These examples are not separate plugin modes; they are factory implementations loaded by `agentseek-langchain`.
- Runtime-specific credentials and services are owned by the example factory or the user-managed remote runtime.
- The DeepAgents example uses repository development dependencies and is not part of the plugin runtime dependency set.
