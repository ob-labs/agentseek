# agentseek-ag-ui

`agentseek-ag-ui` provides an AG-UI channel for the Bub / agentseek `gateway`.

It does not wrap an agent a second time, and it does not run the framework on its own. The intended boundary is:

- register `ag-ui` as a Bub plugin channel;
- let the `gateway` drive the normal hook / state / tool pipeline;
- wrap the parent stream in `channel.stream_events()` and translate Bub / Republic stream events into AG-UI SSE side-channel events.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-ag-ui` |
| Python package | `agentseek_ag_ui` |
| Bub entry point | `ag-ui` |
| Root install path | `uv sync --extra ag-ui` |
| Test target | `make check-ag-ui` |

## Use Cases

This package is a fit when:

- you already run Bub / agentseek through `agentseek gateway`;
- you want AG-UI to participate as a normal channel in the same gateway / hook / state / tool pipeline;
- you want event translation to happen at the channel layer instead of introducing another agent adapter.

The current implementation intentionally stays minimal:

- `POST /agent` accepts AG-UI `RunAgentInput`;
- the channel forwards the request through `on_receive` into the gateway instead of driving the framework locally;
- `stream_events()` maps `text / tool_call / tool_result / usage / error` into AG-UI events;
- `save_state()` only stages the final `STATE_SNAPSHOT` / `model_output` and does not finish the run early.

Current limitations:

- Bub session mapping is currently aligned primarily by `thread_id`;
- `resume` / interrupt semantics are not wired into Bub yet;
- prompt construction currently uses the last user message and prepends `context` as text.

## Installation

From the repository root:

```bash
uv sync --extra ag-ui
```

Or install only this package:

```bash
uv pip install -e contrib/agentseek-ag-ui
```

## Usage

After installation, start the gateway with the `ag-ui` channel enabled:

```bash
uv run agentseek gateway --enable-channel ag-ui
```

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

## Runtime Behavior

- `RunStartedEvent` is emitted when the channel begins wrapping the parent stream;
- `text` stream events become `TEXT_MESSAGE_START` / `TEXT_MESSAGE_CONTENT` / `TEXT_MESSAGE_END`;
- `tool_call` / `tool_result` become the matching AG-UI tool events;
- `usage` is exposed as a `CUSTOM` event named `republic.usage`;
- final state is observed and staged by `save_state()`, then sent on the successful `channel.send()` path;
- `RUN_FINISHED` is emitted only after successful delivery, while failure paths emit `RUN_ERROR`;
- even when the gateway is not streaming, the channel still fills in the minimal terminal sequence on `send()`: `RUN_STARTED` / text / `RUN_FINISHED`, without intermediate tool or usage stream events.

## Verification

```bash
make check-ag-ui
```

Or run it directly:

```bash
uv sync --extra ag-ui
uv run python -m pytest contrib/agentseek-ag-ui/tests
```
