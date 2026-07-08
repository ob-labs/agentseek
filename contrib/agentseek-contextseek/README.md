# agentseek-contextseek

## At A Glance

| | |
|---|---|
| Distribution | `agentseek-contextseek` |
| Python package | `agentseek_contextseek` |
| Bub entry point | `contextseek` |
| Config surface | `AGENTSEEK_CTX_*` env vars |
| Install path | `agentseek plugin install agentseek-contextseek` |
| Test target | `contrib/agentseek-contextseek/tests/` |

## When To Use It

Use this package when you want agent turns to benefit from a semantic memory layer: retrieving relevant past knowledge before each model call and writing new knowledge back afterward. It bridges the agentseek Bub runtime with the [contextseek](https://pypi.org/project/contextseek/) semantic context library.

This package does **not** own contextseek's storage, embedding, or evolution logic — those are contextseek's responsibility.

## Install

Via the agentseek plugin installer (recommended):

```bash
agentseek plugin install agentseek-contextseek
```

Standalone from workspace:

```bash
uv pip install './contrib/agentseek-contextseek'
```

CLI note: `agentseek ctx ...` is part of the main `agentseek` command surface.

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

`agentseek ctx` forwards every sub-command verbatim to the upstream
[`contextseek` CLI](https://pypi.org/project/contextseek/). The verb list,
flags, and exit codes are owned by contextseek; this package does not maintain
a shadow command map. Run `agentseek ctx --help` to see the canonical list.

Common verbs:

```bash
agentseek ctx add      --scope acme/db/eng --content "..." --source wiki
agentseek ctx retrieve --scope acme/db/eng --query "distributed database" --k 5
agentseek ctx overview --scope acme/db/eng
agentseek ctx compact  --scope acme/db/eng
```

Storage directories (e.g. `.contextseek/store`) are created on first write
by the chosen backend — no separate `init` step is required.

### MCP server registration

contextseek ships a stdio MCP server (`contextseek-mcp-stdio`). To expose it
to `bub-mcp` (and any IDE/agent that reads `bub`-style MCP config), add an
entry to your MCP config file. With agentseek defaults that file is
`.agentseek/mcp.json`:

```json
{
  "mcpServers": {
    "contextseek": { "command": "contextseek-mcp-stdio" }
  }
}
```

The server reads `AGENTSEEK_CTX_*` from the project `.env` via
`agentseek_contextseek.config`. When ContextSeek's LLM support is enabled, the
same bridge reuses `BUB_MODEL` / `BUB_API_KEY` / provider-specific Bub
credentials for LangChain env vars, so no environment values need to be
inlined into `mcp.json`.

### HTTP server

contextseek's HTTP API and Python-only DataPlug imports do not (yet) have CLI
entry points upstream. Use the library directly:

```bash
# HTTP
uvicorn contextseek.http.server:create_app --factory --host 127.0.0.1 --port 8001

# DataPlug import
python -c "from contextseek.client.contextseek import ContextSeek; \
           from contextseek.plugs.rag_plug import RagPlug; \
           ContextSeek.from_settings().plug(RagPlug(), scope='acme/db/eng')"
```

## Runtime Behavior

The Bub plugin registers three hooks:

- **`load_state`**: calls `ctx.retrieve(content, scope, k)` and stores a `[ContextSeek]` block in state when retrieval hits.
- **`build_prompt`**: prepends the stored `[ContextSeek]` block to the user prompt (returns `None` when there is no retrieval hit).
- **`save_state`**: calls `ctx.add(model_output, scope, stage=raw)` to feed the model output into the contextseek evolution pipeline.

Scope is derived from Bub state as `{AGENTSEEK_CTX_TENANT}/{chat_id}/{session_id}`.

Both hooks fail silently (debug-level log only) — the semantic layer is enhancement, not a blocking dependency.

The contextseek client is initialized lazily on the first hook invocation, so starting agentseek without contextseek installed does not cause a startup error.

## Verify

```bash
pytest contrib/agentseek-contextseek/tests/
```

## Limitations

- `before_model` uses `trylast=True`, meaning it runs after other non-`trylast` hooks. If another hook modifies the prompt before this one, the injected context will be appended to the already-modified prompt.
- The scope granularity is `tenant/chat_id/session_id`. Context does not automatically propagate across sessions; use a contextseek DataPlug or direct `ctx.add` calls to seed cross-session context.
- Synchronous contextseek client calls are offloaded to a thread pool via `asyncio.to_thread` to avoid blocking the event loop.
