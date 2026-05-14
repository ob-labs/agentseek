# agentseek-ag-ui

`agentseek-ag-ui` provides an AG-UI channel for the Bub / agentseek `gateway`.

It does not own the agent or run the framework on its own. It registers `ag-ui` as a Bub channel and translates Bub / Republic stream events into AG-UI SSE events.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-ag-ui` |
| Python package | `agentseek_ag_ui` |
| Bub entry point | `ag-ui` |
| Root install path | `uv sync --extra ag-ui` |
| Test target | `make check-ag-ui` |

## When To Use It

Use this package when:

- you already run Bub / agentseek through `agentseek gateway`;
- you want AG-UI to participate as a normal channel in the same gateway / hook / state / tool pipeline;
- you want event translation to happen at the channel layer instead of introducing another agent adapter.

It does not:

- construct or own the underlying agent;
- choose a model provider;
- replace Bub state with an AG-UI-specific runtime state model.

Runtime boundary:

- `POST /agent` accepts AG-UI `RunAgentInput`;
- the channel forwards the request through `on_receive` into the gateway instead of driving the framework locally;
- `stream_events()` maps `text / tool_call / tool_result / usage / error` into AG-UI events;
- `load_state()` exposes frontend application state as normal Bub state and stores
  AG-UI transport metadata under a private `_ag_ui` key for downstream adapters;
- `save_state()` only stages the final `STATE_SNAPSHOT` / `model_output` and does not finish the run early.

## Install

From the repository root:

```bash
uv sync --extra ag-ui
```

Or install only this package:

```bash
uv pip install -e contrib/agentseek-ag-ui
```

## Configure

Default bind settings:

- host: `127.0.0.1`
- port: `8088`
- endpoint: `/agent`
- health: `/agent/health`

Supported environment variables:

| agentseek variable | Bub variable | Default | Purpose |
| --- | --- | --- | --- |
| `AGENTSEEK_AG_UI_HOST` | `BUB_AG_UI_HOST` | `127.0.0.1` | HTTP bind host |
| `AGENTSEEK_AG_UI_PORT` | `BUB_AG_UI_PORT` | `8088` | HTTP bind port |
| `AGENTSEEK_AG_UI_PATH` | `BUB_AG_UI_PATH` | `/agent` | AG-UI endpoint path |
| `AGENTSEEK_AG_UI_HEALTH_PATH` | `BUB_AG_UI_HEALTH_PATH` | `/agent/health` | Health endpoint path |
| `AGENTSEEK_STREAM_OUTPUT` | `BUB_STREAM_OUTPUT` | `false` | `true`: stream model output to channels (useful for AG-UI clients). |

`BUB_STREAM_OUTPUT` (default `false`) switches the gateway to `run_model_stream` so this channel can emit deltas. With it off, the run still completes over SSE via `send()`, usually as a single text block. Under agentseek, `AGENTSEEK_STREAM_OUTPUT` is copied to `BUB_STREAM_OUTPUT` only when `BUB_STREAM_OUTPUT` is unset.

## Run

```bash
export AGENTSEEK_STREAM_OUTPUT=true   # recommended for streaming UIs; or BUB_STREAM_OUTPUT=true
uv run agentseek gateway --enable-channel ag-ui
```

## Runtime Behavior

- `RunStartedEvent` is emitted when the channel begins wrapping the parent stream;
- `text` stream events become `TEXT_MESSAGE_START` / `TEXT_MESSAGE_CONTENT` / `TEXT_MESSAGE_END`;
- `tool_call` / `tool_result` become the matching AG-UI tool events;
- `usage` is exposed as a `CUSTOM` event named `republic.usage`;
- final state is observed and staged by `save_state()`, then sent on the successful `channel.send()` path;
- `RUN_FINISHED` is emitted only after successful delivery, while failure paths emit `RUN_ERROR`;
- with `BUB_STREAM_OUTPUT=false`, live deltas from `stream_events()` are absent; the channel still closes the SSE on `send()` with `RUN_STARTED` / text / `RUN_FINISHED`.

## Verify

```bash
make check-ag-ui
```

Or run it directly:

```bash
uv sync --extra ag-ui
uv run python -m pytest contrib/agentseek-ag-ui/tests
```

## Limitations

- Bub session mapping is currently aligned primarily by `thread_id`.
- `resume` / interrupt semantics are not wired into Bub yet.
- Prompt construction is only a fallback path for prompt-only agents: it uses the last user message and prepends only plain scalar `context` values as text, while structured AG-UI metadata stays under `_ag_ui` for downstream integrations.
