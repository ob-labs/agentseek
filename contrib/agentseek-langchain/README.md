# agentseek-langchain

`agentseek-langchain` is a Bub/agentseek plugin that delegates model turns to a LangChain `Runnable` you provide.

It does not introduce a new agent wrapper or own your model credentials. Its job is narrow:

- load a `RunnableSpec` from configuration;
- convert Bub turn state into runnable input and config;
- normalize runnable output into the text result Bub expects.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-langchain` |
| Python package | `agentseek_langchain` |
| Bub entry point | `langchain` |
| Config surface | `AGENTSEEK_LANGCHAIN_SPEC` (agentseek alias) or `BUB_LANGCHAIN_SPEC` |
| Root install path | `uv sync --extra langchain` |
| Test target | `make check-langchain` |

## When To Use It

Use it when:

- you already have a LangChain runnable, agent, or compiled graph that should own turn execution;
- you want agentseek / Bub transport, channels, and persistence to stay in place around that runnable;
- you want AG-UI request state to arrive as normal LangChain messages, tools, and runtime context where possible.

It does not:

- build an agent for you;
- choose a model provider for you;
- force your code into an agentseek-specific middleware or wrapper shape.

## Install

From the repository root:

```bash
uv sync --extra langchain
```

Or install only this package:

```bash
uv pip install -e contrib/agentseek-langchain
```

## Configure

Set one spec path:

```bash
export AGENTSEEK_LANGCHAIN_SPEC=my_project.agent_binding:SPEC
```

`agentseek` maps `AGENTSEEK_LANGCHAIN_SPEC` to Bub’s native `BUB_LANGCHAIN_SPEC`, so either name works. `SPEC` must resolve to:

- A `RunnableSpec` object, or
- A zero-argument factory function that returns a `RunnableSpec`

The plugin does not accept a bare runnable export. Input and output shapes must be declared explicitly in `RunnableSpec`.

## Run

Minimal binding:

```python
from langchain.agents import create_agent

from agentseek_langchain import messages_spec


agent = create_agent(
    model="openai:gpt-4.1",
    tools=[],
)

SPEC = messages_spec(agent)
```

Then point the gateway at that binding and start it normally:

```bash
export AGENTSEEK_LANGCHAIN_SPEC=my_project.agent_binding:SPEC
uv run agentseek gateway
```

Common runnable shapes:

- `messages_spec(...)`: messages/state-style runnables such as `create_agent()`, `StateGraph.compile()`, and `create_deep_agent()`
- `text_spec(...)`: prompt-in / text-out runnables
- `LangGraphClientRunnable(...)`: remote LangGraph SDK client bridge

### LangGraph

```python
from langgraph.graph import StateGraph

from agentseek_langchain import messages_spec

graph = StateGraph(...)
compiled = graph.compile()

SPEC = messages_spec(compiled)
```

### DeepAgents

```python
from deepagents import create_deep_agent

from agentseek_langchain import messages_spec

deep_agent = create_deep_agent(...)

SPEC = messages_spec(deep_agent)
```

### LangGraph SDK Client

```python
from langgraph_sdk import get_client
from agentseek_langchain import LangGraphClientRunnable, messages_spec

client = get_client(url="http://127.0.0.1:8123")
runnable = LangGraphClientRunnable(client, assistant_id="agent")

SPEC = messages_spec(runnable)
```

`LangGraphClientRunnable` only translates `ainvoke(...)` into `client.runs.wait(...)`. Input and output shapes are still determined by `messages_spec(...)` / `text_spec(...)`.

## Runtime Behavior

- When this plugin loads successfully, `run_model` / `run_model_stream` register with `tryfirst=True`, so the LangChain spec runs before Bub’s built-in model agent.
- For AG-UI turns, the plugin rebuilds LangChain messages, frontend-declared tools, and CopilotKit context from the private `_ag_ui` state staged by `agentseek-ag-ui`.
- If your runnable supports LangChain runtime `context=...` (for example `create_agent(..., context_schema=...)`), AG-UI context is forwarded there automatically.
- If the runnable returns `structured_response`, the package serializes it into JSON text so the surrounding transport can decide how to render it.
- `messages_spec(...)` decides whether `AGENTS.md` is injected; the plugin only reads it and places it on `InvocationContext.agents_md`.

## Verify

```bash
make check-langchain
```

Or run it directly:

```bash
uv sync --extra langchain
uv run python -m pytest contrib/agentseek-langchain/tests
```

## Limitations

- This package only understands the shapes declared through `RunnableSpec`; a bare runnable export is rejected.
- `text_spec(...)` is intentionally narrow and does not accept multimodal prompt input.
- Structured UI still depends on the runnable and model provider being able to satisfy the schema you pass in at runtime.
