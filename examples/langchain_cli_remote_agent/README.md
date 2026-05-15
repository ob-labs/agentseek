# Connect a `langgraph dev` Remote Agent to agentseek

This is a **How-to Guide**. Its purpose is to take a LangChain agent served by
`langgraph dev`, connect it to `agentseek`, and verify the integration with a real
`uv run agentseek run` request.

## What You Will Get

When you finish, you will have this call chain:

```text
uv run agentseek run
  -> agentseek-langchain
    -> LangGraphClientRunnable
      -> langgraph_sdk client
        -> uv run langgraph dev
          -> create_agent(...)
```

The binding export is:

```text
examples.langchain_cli_remote_agent.gateway_binding:build_spec
```

## What Problem This Example Solves

Use this example when you already have a standard LangChain agent and you want:

- the agent to remain served by `langgraph dev`;
- `agentseek` to handle the local CLI / gateway / runtime entry point;
- the remote Agent Server request to contain only the state that the remote graph actually needs.

This example therefore does **not** directly reuse the generic `messages_spec(..., as_state=True)`
path. Instead, it builds an example-local **messages-only state dict**:

```python
{"messages": [...]}
```

That keeps local Bub runtime objects such as `mcp` out of the JSON request while still matching
the input shape expected by the remote `create_agent(...)` graph.

## Files in This Example

| File | Purpose |
| --- | --- |
| [`remote_graph.py`](remote_graph.py) | The LangChain agent loaded by the remote `langgraph dev` process. |
| [`langgraph.json`](langgraph.json) | LangGraph CLI config that exports the graph id `agent`. |
| [`gateway_binding.py`](gateway_binding.py) | The agentseek-side remote bridge binding. |
| [`settings.py`](settings.py) | Shared environment settings for the remote agent and the local bridge. |
| [`requirements.txt`](requirements.txt) | Extra Python dependencies required by this example. |

## Step 1: Install Dependencies

Run from the repository root:

```bash
uv sync --extra langchain
uv pip install -r examples/langchain_cli_remote_agent/requirements.txt
```

## Step 2: Start the Remote Agent

In the first terminal, reuse the existing model configuration and start `langgraph dev`:

```bash
set -a
source examples/ag_ui_langchain/.env
set +a
cd examples/langchain_cli_remote_agent
uv run langgraph dev
```

By default, the server starts at:

```text
http://127.0.0.1:2024
```

The graph id is:

```text
agent
```

## Step 3: Point agentseek at the Remote Agent

In the second terminal, return to the repository root and run this tested command:

```bash
set -a
source examples/ag_ui_langchain/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.langchain_cli_remote_agent.gateway_binding:build_spec
export LANGGRAPH_URL=http://127.0.0.1:2024
export LANGGRAPH_ASSISTANT_ID=agent
uv run --no-sync --no-env-file agentseek run \
  "Plan a low-risk rollout for enabling a new read path behind a feature flag." \
  --session-id langgraph-remote-demo
```

Three details matter here:

- `PYTHONPATH=.` lets Python import `examples.langchain_cli_remote_agent.gateway_binding` from the repository root.
- `LANGGRAPH_URL` points to the local Agent Server.
- `LANGGRAPH_ASSISTANT_ID=agent` must match the graph id defined in [`langgraph.json`](langgraph.json).

## Why This Example Does Not Use Generic `messages_spec(...)`

The remote `create_agent(...)` graph expects a state dict, not a bare list of messages.

So this example adds a small local adapter in [`gateway_binding.py`](gateway_binding.py):

```python
from agentseek_langchain import LangGraphClientRunnable, RunnableSpec, default_runnable_config
from agentseek_langchain.ag_ui import langchain_messages_from_state
from agentseek_langchain.profiles import parse_messages_output
from langchain_core.messages import HumanMessage, SystemMessage


def _build_remote_input(context):
    messages = langchain_messages_from_state(context.state)
    if not messages:
        messages = [HumanMessage(content=context.prompt)]
    if context.agents_md:
        messages = [SystemMessage(content=context.agents_md), *messages]
    return {"messages": messages}
```

That adapter is then wired into a `RunnableSpec`:

```python
def build_spec():
    client = get_client(url="http://127.0.0.1:2024")
    runnable = LangGraphClientRunnable(client, assistant_id="agent")
    return RunnableSpec(
        runnable=runnable,
        build_input=_build_remote_input,
        parse_output=parse_messages_output,
        build_config=default_runnable_config,
    )
```

Source: [`gateway_binding.py`](gateway_binding.py)

## Step 4: Serve It Through the Gateway

The same binding can also be used behind `agentseek gateway`:

```bash
set -a
source examples/ag_ui_langchain/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.langchain_cli_remote_agent.gateway_binding:build_spec
export LANGGRAPH_URL=http://127.0.0.1:2024
export LANGGRAPH_ASSISTANT_ID=agent
uv run --no-sync --no-env-file agentseek gateway
```

## Verify

Syntax and config checks:

```bash
uv run --no-sync python -m compileall examples/langchain_cli_remote_agent
uv run --no-sync python -m json.tool examples/langchain_cli_remote_agent/langgraph.json >/dev/null
```

Runtime check:

```bash
uv run --no-sync --no-env-file agentseek run \
  "Plan a low-risk rollout for enabling a new read path behind a feature flag." \
  --session-id langgraph-remote-demo
```

If the output clearly comes from the remote agent instead of the built-in local model path, the
integration is working.

## When Not to Use This Example

This example is not the right fit when:

- You are connecting a local `create_deep_agent(...)` runnable.
- You need to forward the full Bub application state into the remote graph.
- You want architecture explanation instead of the shortest working setup path.

Related examples:

- Local DeepAgents: [`../langchain_deepagents/README.md`](../langchain_deepagents/README.md)
- AG-UI + LangChain: [`../ag_ui_langchain/README.md`](../ag_ui_langchain/README.md)
