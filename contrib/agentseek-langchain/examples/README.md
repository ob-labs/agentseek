# LangChain Examples

These are bundled factories for `agentseek-langchain`.

The runnable modules live under `examples/agentseek_langchain_examples/` and are loaded through
`AGENTSEEK_LANGCHAIN_FACTORY`.

Each factory returns `RunnableBinding`.
Each factory accepts `request: LangchainFactoryRequest`.

## Prerequisites

From the repo root:

```bash
uv sync --all-packages
```

For the DashScope DeepAgents example, install the extra runtime deps if they are not already present:

```bash
uv pip install -e 'contrib/agentseek-langchain[deepagents]'
```

## Minimal Runnable

Factory path:

```bash
agentseek_langchain_examples.minimal_runnable:minimal_lc_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_MODE=runnable
export AGENTSEEK_LANGCHAIN_FACTORY=agentseek_langchain_examples.minimal_runnable:minimal_lc_agent
```

Run it:

```bash
uv run agentseek chat
uv run agentseek run "Summarize this workspace in one sentence."
```

## DeepAgents + DashScope

Factory path:

```bash
agentseek_langchain_examples.deepagents_dashscope:dashscope_deep_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_MODE=runnable
export AGENTSEEK_LANGCHAIN_FACTORY=agentseek_langchain_examples.deepagents_dashscope:dashscope_deep_agent
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

## Remote Agent Protocol

Factory path:

```bash
agentseek_langchain_examples.remote_agent_protocol:remote_agent_protocol_agent
```

Enable it:

```bash
export AGENTSEEK_LANGCHAIN_MODE=runnable
export AGENTSEEK_LANGCHAIN_FACTORY=agentseek_langchain_examples.remote_agent_protocol:remote_agent_protocol_agent
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
