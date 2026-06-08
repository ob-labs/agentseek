# Connect an `agentseek-api` Remote Agent to agentseek

This is a **How-to Guide**. Its purpose is to take a LangChain agent served by
`agentseek api serve`, connect it to `agentseek`, and verify the integration
with a real `uv run agentseek turn` request.

## What You Will Get

When you finish, you will have this call chain:

```text
uv run agentseek turn
  -> agentseek-langchain
    -> LangGraphClientRunnable
      -> langgraph_sdk client
        -> uv run agentseek api serve
          -> agentseek-api
            -> create_agent(...)
```

The binding export is:

```text
examples.agentseek_api_remote_agent.gateway_binding:build_spec
```

## What Problem This Example Solves

Use this example when:

- you want to keep a LangChain agent behind an HTTP runtime instead of a local
  in-process runnable;
- you want the remote runtime to be `agentseek-api`, not `langgraph dev`;
- you still want local `agentseek` transport, CLI, and gateway behavior around
  that remote runtime.

Like the `langchain/cli-remote` template, this bridge sends a compact
messages-only state dict:

```python
{"messages": [...]}
```

That keeps local Bub runtime objects such as `mcp` out of the remote JSON
payload while still matching the remote graph input shape.

## Files in This Example

| File | Purpose |
| --- | --- |
| [`remote_graph.py`](remote_graph.py) | The LangChain agent loaded by the remote `agentseek-api` process. |
| [`agentseek.json`](agentseek.json) | `agentseek-api` manifest that exports the graph id `agent`. |
| [`gateway_binding.py`](gateway_binding.py) | The agentseek-side remote bridge binding. |
| [`settings.py`](settings.py) | Shared environment settings for the remote agent and the local bridge. |
| [`requirements.txt`](requirements.txt) | Extra Python dependencies required by this example. |

## Step 1: Install Dependencies

Run from the repository root:

```bash
uv sync --extra langchain
uv pip install -e references/agentseek-api
uv pip install -r examples/agentseek_api_remote_agent/requirements.txt
cp examples/agentseek_api_remote_agent/.env.example examples/agentseek_api_remote_agent/.env
# edit .env to set AGENTSEEK_MODEL, AGENTSEEK_API_KEY, AGENTSEEK_API_BASE
```

## Step 2: Prepare a SeekDB-Compatible Checkpoint Backend

`agentseek-api` currently still initializes an OceanBase / SeekDB-compatible
checkpointer even when metadata storage is moved to SQLite. For local
development, the simplest substitute is SeekDB.

For a repeatable local setup, start a dedicated SeekDB container first:

```bash
docker run -d --rm \
  --name agentseek-seekdb-demo \
  -p 2883:2881 \
  -e SEEKDB_DATABASE=seekdb \
  oceanbase/seekdb:latest

export OCEANBASE_HOST=127.0.0.1
export OCEANBASE_PORT=2883
export OCEANBASE_USER=root
export OCEANBASE_PASSWORD=
export OCEANBASE_DB_NAME=seekdb
export SEEKDB_URL=mysql+aiomysql://root:@127.0.0.1:2883/seekdb
```

This is the flow validated in this repository. If you already have OceanBase or
another SeekDB endpoint, you can reuse it, but adjust the host, port, user, and
database name to match the actual deployment.

## Step 3: Start the Remote API Runtime

In the first terminal, reuse the existing model configuration and start
`agentseek-api` through the `agentseek api` passthrough:

```bash
mkdir -p .tmp
set -a
source examples/agentseek_api_remote_agent/.env
set +a
export METADATA_DB_URL=sqlite+aiosqlite:///$(pwd)/.tmp/agentseek-api-example.db
export METADATA_DB_BACKEND=sqlite
cd examples/agentseek_api_remote_agent
uv run --no-sync --no-env-file agentseek api serve \
  --config ./agentseek.json \
  --host 127.0.0.1 \
  --port 2024
```

By default, the server starts at:

```text
http://127.0.0.1:2024
```

The graph id is:

```text
agent
```

The local bridge will search for an assistant named `agentseek-api-demo` under
that graph id, and create it automatically if it does not exist yet.

## Step 4: Point agentseek at the Remote Runtime

In the second terminal, return to the repository root and run this command:

```bash
set -a
source examples/agentseek_api_remote_agent/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.agentseek_api_remote_agent.gateway_binding:build_spec
export AGENTSEEK_API_REMOTE_URL=http://127.0.0.1:2024
export AGENTSEEK_API_REMOTE_GRAPH_ID=agent
export AGENTSEEK_API_REMOTE_ASSISTANT_NAME=agentseek-api-demo
export AGENTSEEK_API_REMOTE_USER_ID=dev
uv run --no-sync --no-env-file agentseek turn \
  "Plan a low-risk rollout for enabling a new read path behind a feature flag." \
  --session-id agentseek-api-remote-demo
```

Four details matter here:

- `PYTHONPATH=.` lets Python import
  `examples.agentseek_api_remote_agent.gateway_binding` from the repository
  root.
- `AGENTSEEK_API_REMOTE_URL` points to the remote `agentseek-api` runtime.
- `AGENTSEEK_API_REMOTE_GRAPH_ID=agent` must match the graph id defined in
  [`agentseek.json`](agentseek.json).
- `AGENTSEEK_API_REMOTE_USER_ID=dev` becomes the `x-user-id` header used for
  assistant lookup and run submission.

## Why This Example Resolves the Assistant Automatically

The remote runtime speaks through the assistant resource model, not through a
raw graph id alone.

So the bridge does one extra piece of setup in [`gateway_binding.py`](gateway_binding.py):

```python
def _resolve_assistant_id(settings):
    if settings.assistant_id.strip():
        return settings.assistant_id

    with get_sync_client(url=settings.api_url, headers=settings.request_headers()) as client:
        assistants = client.assistants.search(
            name=settings.assistant_name,
            graph_id=settings.graph_id,
            limit=1,
        )
        if assistants:
            return str(assistants[0]["assistant_id"])

        created = client.assistants.create(
            graph_id=settings.graph_id,
            name=settings.assistant_name,
            metadata={"source": "examples.agentseek_api_remote_agent"},
        )
        return str(created["assistant_id"])
```

That assistant id is then passed into `LangGraphClientRunnable(...)` before the
normal `RunnableSpec` wiring happens.

## Step 5: Serve It Through the Gateway

The same binding can also be used behind `agentseek gateway`:

```bash
set -a
source examples/agentseek_api_remote_agent/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.agentseek_api_remote_agent.gateway_binding:build_spec
export AGENTSEEK_API_REMOTE_URL=http://127.0.0.1:2024
export AGENTSEEK_API_REMOTE_GRAPH_ID=agent
export AGENTSEEK_API_REMOTE_ASSISTANT_NAME=agentseek-api-demo
export AGENTSEEK_API_REMOTE_USER_ID=dev
uv run --no-sync --no-env-file agentseek gateway
```

## Verify

Syntax and config checks:

```bash
uv run --no-sync python -m compileall examples/agentseek_api_remote_agent
uv run --no-sync python -m json.tool examples/agentseek_api_remote_agent/agentseek.json >/dev/null
```

Runtime check:

```bash
set -a
source examples/agentseek_api_remote_agent/.env
set +a
export PYTHONPATH=.
export AGENTSEEK_LANGCHAIN_SPEC=examples.agentseek_api_remote_agent.gateway_binding:build_spec
export AGENTSEEK_API_REMOTE_URL=http://127.0.0.1:2024
export AGENTSEEK_API_REMOTE_GRAPH_ID=agent
export AGENTSEEK_API_REMOTE_ASSISTANT_NAME=agentseek-api-demo
export AGENTSEEK_API_REMOTE_USER_ID=dev
uv run --no-sync --no-env-file agentseek turn \
  "Plan a low-risk rollout for enabling a new read path behind a feature flag." \
  --session-id agentseek-api-remote-demo
```

If the output clearly comes from the remote agent instead of the built-in local
model path, the integration is working.

Cleanup after the demo:

```bash
docker rm -f agentseek-seekdb-demo
```

## When Not to Use This Example

This example is not the right fit when:

- you want a pure `langgraph dev` demo;
- you need a fully in-process local runnable;
- you want to avoid a SeekDB / OceanBase-compatible checkpoint backend entirely.

Related examples:

- OTEL sidecar: [`../langchain_otel_sidecar/README.md`](../langchain_otel_sidecar/README.md)
