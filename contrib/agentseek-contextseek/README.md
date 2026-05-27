# agentseek-contextseek

## At A Glance

| | |
|---|---|
| Distribution | `agentseek-contextseek` |
| Python package | `agentseek_contextseek` |
| Bub entry point | `contextseek` |
| Config surface | `AGENTSEEK_CTX_*` env vars |
| Install path | `uv sync --extra context` or `uv pip install 'agentseek[context]'` |
| Test target | `contrib/agentseek-contextseek/tests/` |

## When To Use It

Use this package when you want agent turns to benefit from a semantic memory layer: retrieving relevant past knowledge before each model call and writing new knowledge back afterward. It bridges the agentseek Bub runtime with the [contextseek](https://pypi.org/project/contextseek/) semantic context library.

This package does **not** own contextseek's storage, embedding, or evolution logic — those are contextseek's responsibility.

## Install

Via agentseek optional extra (recommended):

```bash
uv pip install 'agentseek[context]'
```

Standalone from workspace:

```bash
uv pip install './contrib/agentseek-contextseek'
```

CLI note: `agentseek ctx ...` commands are provided by
[`agentseek-cli`](../agentseek-cli/README.md). In workspace/dev installs, use:

```bash
uv sync --extra context
```

## Configure

All contextseek env vars can be set with the `AGENTSEEK_CTX_` prefix. These act as fallbacks — if you have already set a raw contextseek variable (e.g. `STORAGE_BACKEND`), it takes precedence.

| AGENTSEEK_CTX_* variable | Maps to | Default |
|---|---|---|
| `AGENTSEEK_CTX_STORAGE_BACKEND` | `STORAGE_BACKEND` | `memory` |
| `AGENTSEEK_CTX_STORAGE_PATH` | `STORAGE_PATH` | `.contextseek/store` |
| `AGENTSEEK_CTX_OB_HOST` | `OB_HOST` | `127.0.0.1` |
| `AGENTSEEK_CTX_OB_PORT` | `OB_PORT` | `2881` |
| `AGENTSEEK_CTX_EMBEDDING_MODEL` | `EMBEDDING_MODEL` | _(contextseek default)_ |
| `AGENTSEEK_CTX_LLM_MODEL` | `LLM_MODEL` | _(contextseek default)_ |
| `AGENTSEEK_CTX_EVOLUTION_ENABLED` | `EVOLUTION_ENABLED` | `true` |
| `AGENTSEEK_CTX_RETRIEVAL_DEFAULT_K` | `RETRIEVAL_DEFAULT_K` | `5` |
| `AGENTSEEK_CTX_TENANT` | _(scope prefix)_ | `default` |

See `.env.example` in the repo root for a full list of supported variables.

## Run

Initialize a project (through `agentseek-cli`):

```bash
agentseek ctx init --backend memory
agentseek ctx init --backend oceanbase
```

Retrieve and manage context:

```bash
agentseek ctx add      --scope acme/db/eng --content "..." --source wiki
agentseek ctx retrieve --scope acme/db/eng --query "distributed database" --k 5
agentseek ctx overview --scope acme/db/eng
agentseek ctx compact  --scope acme/db/eng
```

Start the HTTP + MCP server:

```bash
agentseek ctx serve --port 8001 --mcp
```

Batch import from external sources:

```bash
agentseek ctx sync --scope acme/db/eng --source rag --source powermem
agentseek ctx sync --scope acme/db/eng --dry-run
```

## Runtime Behavior

The Bub plugin registers two hooks:

- **`before_model` (`trylast`)**: calls `ctx.retrieve(prompt, scope, k=5)` and injects a `[SeekContext]` block into the system prompt.
- **`after_model`**: calls `ctx.add(response, scope, stage=raw)` to feed the model's response into the contextseek evolution pipeline.

Scope is derived from Bub state as `{AGENTSEEK_CTX_TENANT}/{chat_id}/{session_id}`.

Both hooks fail silently (debug-level log only) — the semantic layer is enhancement, not a blocking dependency.

The contextseek client is initialized lazily on the first hook invocation, so starting agentseek without contextseek installed does not cause a startup error.

## Verify

```bash
pytest contrib/agentseek-contextseek/tests/
```

## Limitations

- `before_model` uses `trylast=True`, meaning it runs after other non-`trylast` hooks. If another hook modifies the prompt before this one, the injected context will be appended to the already-modified prompt.
- The scope granularity is `tenant/chat_id/session_id`. Context does not automatically propagate across sessions; use `agentseek ctx sync` or direct `ctx.add` calls to seed cross-session context.
- Synchronous contextseek client calls are offloaded to a thread pool via `asyncio.to_thread` to avoid blocking the event loop.
