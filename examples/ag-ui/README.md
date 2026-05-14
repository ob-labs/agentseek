# CopilotKit + AG-UI Example (`agentseek-ag-ui`)

This example runs an end-to-end browser chat against `agentseek gateway` with the **AG-UI** channel enabled. The UI is **CopilotKit** (React) talking to a small **Copilot Runtime** (Express); the runtime forwards runs to the gateway using **`@ag-ui/client` `HttpAgent`**. There is no LangChain layer and no extra Python binding.

## At A Glance

| Field | Value |
| --- | --- |
| Stack | CopilotKit frontend + Copilot Runtime + agentseek gateway (`ag-ui` channel) |
| Frontend | `http://127.0.0.1:5173` |
| Runtime | `http://127.0.0.1:4000/api/copilotkit` |
| Gateway | `http://127.0.0.1:8088/agent` |
| Scope | Pure AG-UI transport demo; no LangChain or structured UI layer |

## Architecture

```text
Browser (CopilotKit v2)
  -> Vite dev server :5173  (/api/copilotkit/* proxied)
    -> Copilot Runtime (Express) :4000  /api/copilotkit
      -> HttpAgent (AG-UI client)
        -> agentseek gateway :8088  /agent  (AG-UI channel)
          -> configured agentseek model provider
```

During `npm run dev`, **two processes** start via `concurrently`:

| Process | Port | Role |
| --- | --- | --- |
| `tsx server.ts` | `4000` | CopilotKit runtime (`CopilotRuntime` + `createCopilotExpressHandler`). |
| `vite` | `5173` | React app; proxies `/api/copilotkit` to the runtime. |

The React app uses **`@copilotkit/react-core/v2`** with `runtimeUrl=/api/copilotkit` and **`useSingleEndpoint={false}`**, so the client talks to the multi-route runtime surface instead of a legacy single-endpoint POST.

For **CopilotKit + Hashbrown** structured UI on top of the same gateway stack, use the separate app under [`../ag_ui_langchain/frontend`](../ag_ui_langchain/frontend/README.md) (different ports so this demo stays unchanged).

## Prerequisites

**Python (repo root)** — install the distribution with the AG-UI extra:

```bash
uv sync --extra ag-ui
```

Configure a real model provider for the gateway, for example:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

Optional: `AGENTSEEK_STREAM_OUTPUT=true` (or `BUB_STREAM_OUTPUT=true`) in the environment or repo root `.env` so the assistant streams token-by-token — see **Gateway streaming** below.

**Node.js** — CopilotKit’s dependency tree targets current Node releases; **Node 20+** is recommended. Older versions may still install with engine warnings.

**Frontend dependencies:**

```bash
cd examples/ag-ui/frontend
npm install
```

## Configure

This example only needs normal agentseek model configuration plus the runtime / Vite env documented below.

## Run

**1. Start the gateway** (repository root):

```bash
export AGENTSEEK_STREAM_OUTPUT=true   # recommended; or BUB_STREAM_OUTPUT=true
uv run agentseek gateway --enable-channel ag-ui
```

Default AG-UI URL: **`http://127.0.0.1:8088/agent`** (change if your gateway settings differ).

**2. Start the frontend** (second terminal):

```bash
cd examples/ag-ui/frontend
npm run dev
```

**3. Open** `http://127.0.0.1:5173` and send a message in the chat.

## Runtime Config

### Gateway streaming

`BUB_STREAM_OUTPUT` (default `false`) controls whether the gateway uses `run_model_stream`. Turn it on with `AGENTSEEK_STREAM_OUTPUT=true` or `BUB_STREAM_OUTPUT=true` so `stream_events()` can emit incremental `TEXT_MESSAGE_CONTENT`. Agentseek maps `AGENTSEEK_STREAM_OUTPUT` → `BUB_STREAM_OUTPUT` only if `BUB_STREAM_OUTPUT` is not already set.

| Variable | Notes |
| --- | --- |
| `AGENTSEEK_STREAM_OUTPUT` | `true` enables streaming for the process (via alias above). |
| `BUB_STREAM_OUTPUT` | Same meaning; if set explicitly, it overrides the agentseek alias. |

### Runtime → gateway (`server.ts`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `COPILOTKIT_PORT` | `4000` | Port for the Express Copilot runtime. |
| `AGENTSEEK_AG_UI_AGENT_URL` | `http://127.0.0.1:8088/agent` | URL passed to `HttpAgent`; must match where the gateway exposes AG-UI. |

Health check (runtime only):

```bash
curl -s http://127.0.0.1:4000/health
```

### Vite dev proxy (`vite.config.ts`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_COPILOTKIT_RUNTIME_PROXY` | `http://127.0.0.1:4000` | Upstream for proxying browser requests to `/api/copilotkit/*`. |
| `VITE_AGENTSEEK_AG_UI_URL` | `http://127.0.0.1:8088` | Proxy target for `/agent` (useful for direct AG-UI debugging; normal chat traffic goes through the runtime). |

### React app

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_COPILOTKIT_RUNTIME_URL` | `/api/copilotkit` | `CopilotKit` `runtimeUrl` (under dev, resolved via Vite to the runtime). |

**Example:** gateway AG-UI on another host/port — set the same target for the runtime and (if needed) Vite:

```bash
export AGENTSEEK_AG_UI_AGENT_URL=http://127.0.0.1:9090/agent
# optional if you also need /agent in the browser during dev:
export VITE_AGENTSEEK_AG_UI_URL=http://127.0.0.1:9090
cd examples/ag-ui/frontend
npm run dev
```

## Verify

Build the production bundle:

```bash
cd examples/ag-ui/frontend
npm run build
```

Smoke checks with dev servers running:

- Runtime: `curl -s http://127.0.0.1:4000/health` should report `status: ok` and the configured `agent` URL.
- Through Vite: open `http://127.0.0.1:5173` and confirm chat streams; the first request after startup may race if Vite starts before the runtime — refresh once if you see a transient proxy error.

`npm run preview` only serves the static Vite build; for a full chat you still need the **runtime** (`tsx server.ts` or your own deployment) and the **gateway**.

## Troubleshooting

- **`runtime_info_fetch_failed` or 404 on `/api/copilotkit`:** ensure imports are from **`@copilotkit/react-core/v2`** and `useSingleEndpoint={false}` matches the multi-route Express handler.
- **`ECONNREFUSED 127.0.0.1:4000` in the Vite log:** the runtime is not up yet or `COPILOTKIT_PORT` / `VITE_COPILOTKIT_RUNTIME_PROXY` are mismatched.
- **Empty or hanging chat:** confirm the gateway is running and `AGENTSEEK_AG_UI_AGENT_URL` points at the live `/agent` URL.
- **Reply appears in one block:** set `AGENTSEEK_STREAM_OUTPUT=true` or `BUB_STREAM_OUTPUT=true` and restart the gateway (see **Gateway streaming**).

## Limitations

- Demo-sized UI and wiring, not a production deployment guide.
- Requires a working agentseek model configuration; no bundled fake model.
- This example demonstrates AG-UI transport and streaming, not schema-driven generative UI rendering.

## Related paths

| Piece | Path |
| --- | --- |
| AG-UI channel | [`../../contrib/agentseek-ag-ui`](../../contrib/agentseek-ag-ui) |
| CopilotKit frontend | [`frontend`](frontend) |
| LangChain + Hashbrown UI (separate Vite app) | [`../ag_ui_langchain/frontend/README.md`](../ag_ui_langchain/frontend/README.md) |
