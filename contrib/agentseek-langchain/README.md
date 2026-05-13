# agentseek-langchain

`agentseek-langchain` is a Bub/agentseek plugin that delegates `run_model` to a LangChain `Runnable` you provide.

This package does not provide a new agent wrapper, manage model configuration for you, or assume which higher-level framework you use. It does three things:

- Loads a `RunnableSpec` from an environment variable
- Converts Bub turn context into runnable input/config
- Normalizes runnable output into the text result Bub expects

## Installation

In this repository, it is a workspace member. When published separately, install it like a regular Bub plugin.

## Configuration

The plugin requires one environment variable:

```bash
export AGENTSEEK_LANGCHAIN_SPEC=my_project.agent_binding:SPEC
```

`SPEC` must be:

- A `RunnableSpec` object, or
- A zero-argument factory function that returns a `RunnableSpec`

The plugin does not accept a bare runnable export. Input and output shapes must be declared explicitly in `RunnableSpec`.

### Hook precedence

When this plugin loads successfully, `run_model` / `run_model_stream` are registered with **`tryfirst=True`** so your LangChain spec runs **before** Bub’s built-in model agent. To use the builtin agent instead, do not install this plugin or unset / fix `BUB_LANGCHAIN_SPEC` so the plugin fails to initialize.

## Usage

### LangChain Agent

```python
from langchain.agents import create_agent

from agentseek_langchain import messages_spec

agent = create_agent(
    model="openai:gpt-4.1",
    tools=[],
)

SPEC = messages_spec(agent)
```

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

`LangGraphClientRunnable` only translates `ainvoke(...)` into `client.runs.wait(...)`.
Input and output shapes are still determined by `messages_spec(...)` / `text_spec(...)`.

## Design Boundaries

- `messages_spec(...)` is intended for messages/state-style runnables such as `create_agent()`, `StateGraph.compile()`, and `create_deep_agent()`
- `text_spec(...)` is intended for runnables whose input and output are both close to plain text
- `LangGraphClientRunnable(...)` is intended for the remote client path based on `from langgraph_sdk import get_client`

By default, the plugin reads the workspace `AGENTS.md` and stores it in `InvocationContext.agents_md`, but whether it is actually injected into runnable input is decided by the specific `RunnableSpec`.
