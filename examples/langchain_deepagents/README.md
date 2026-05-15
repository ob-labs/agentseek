# Connect DeepAgents to agentseek

This is a **How-to Guide**. Its purpose is not to explain all of DeepAgents or all of
agentseek. Its purpose is to help you wire a local `create_deep_agent(...)` runnable into
`agentseek` through `agentseek-langchain` and verify that the integration actually works.

## What You Will Get

When you finish, you will have a working call chain:

```text
uv run agentseek run
  -> agentseek-langchain
    -> messages_spec(...)
      -> create_deep_agent(...)
```

The binding export is:

```text
examples.langchain_deepagents.demo_binding:build_spec
```

## Before You Start

- You are in the repository root.
- You already have working model/provider credentials.
- You want to connect a **local** DeepAgents runnable to agentseek, not a remote LangGraph Agent Server.

## Files in This Example

| File | Purpose |
| --- | --- |
| [`demo_binding.py`](demo_binding.py) | Builds `create_deep_agent(...)` and exports `build_spec()`. |
| [`settings.py`](settings.py) | Reads example environment variables and bridges `AGENTSEEK_*` into `OPENAI_*` when needed. |
| [`requirements.txt`](requirements.txt) | Extra Python dependencies required by this example. |

## Step 1: Install Dependencies

Run from the repository root:

```bash
uv sync --extra langchain
uv pip install -r examples/langchain_deepagents/requirements.txt
```

## Step 2: Prepare Environment Variables

This example reuses the existing [`examples/ag_ui_langchain/.env`](../ag_ui_langchain/.env).

```bash
set -a
source examples/ag_ui_langchain/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.langchain_deepagents.demo_binding:build_spec
```

Two details matter here:

- `PYTHONPATH=.` lets Python import `examples.langchain_deepagents.demo_binding` from the repository root.
- `AGENTSEEK_LANGCHAIN_SPEC=...:build_spec` tells `agentseek` to delegate model turns to this example binding.

## Step 3: Run One Request

This command has been tested end-to-end:

```bash
uv run --no-sync --no-env-file agentseek run \
  "Design a rollback-safe plan for adding a nullable column to a hot table." \
  --session-id deepagents-demo
```

If the reply clearly comes from the DeepAgents runnable rather than the built-in agentseek
model path, the integration is working.

## Step 4: Serve It Through the Gateway

The same binding also works behind the HTTP gateway:

```bash
set -a
source examples/ag_ui_langchain/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.langchain_deepagents.demo_binding:build_spec
uv run --no-sync --no-env-file agentseek gateway
```

## Smallest Useful Binding

The core binding is only two layers:

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

Source: [`demo_binding.py`](demo_binding.py)

## Verify

Syntax-only check:

```bash
uv run --no-sync python -m compileall examples/langchain_deepagents
```

Runtime check:

```bash
uv run --no-sync --no-env-file agentseek run \
  "Design a rollback-safe plan for adding a nullable column to a hot table." \
  --session-id deepagents-demo
```

## When Not to Use This Example

This example is not the right fit when:

- You are connecting a remote `langgraph dev` or Agent Server deployment.
- You need AG-UI / CopilotKit state to flow into the runnable.
- You want general reference documentation instead of the shortest working path.

Related examples:

- Remote LangGraph: [`../langchain_cli_remote_agent/README.md`](../langchain_cli_remote_agent/README.md)
- AG-UI + LangChain: [`../ag_ui_langchain/README.md`](../ag_ui_langchain/README.md)
