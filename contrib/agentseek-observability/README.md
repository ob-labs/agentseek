# agentseek-observability

`agentseek-observability` is a Bub/agentseek plugin that adds Logfire-backed spans across the `any-llm -> republic -> bub` runtime path.

## At A Glance

| Field | Value |
| --- | --- |
| Distribution | `agentseek-observability` |
| Python package | `agentseek_observability` |
| Bub entry point | `observability` |
| Config surface | Logfire's native `LOGFIRE_*` / `OTEL_*` environment variables |
| Root install path | `uv sync --extra observability` |
| Test target | `uv run python -m pytest contrib/agentseek-observability/tests` |

## When To Use It

Use it when:

- you want one trace tree that starts from Bub turn execution and reaches down into Republic and any-llm;
- you already use Logfire or another OTLP-compatible backend such as Jaeger;
- you want span data without forking Bub, Republic, or any-llm.

It does not:

- replace Logfire configuration or token management;
- own your exporter endpoint, sampling, or retention policy;
- re-implement provider-specific tracing that Logfire already ships for other SDKs.

## Install

From the repository root:

```bash
uv sync --extra observability
```

Or install only this package:

```bash
uv pip install -e contrib/agentseek-observability
```

## Configure

This package reuses Logfire's native configuration. Common local Jaeger setup:

```bash
export LOGFIRE_SEND_TO_LOGFIRE=false
export LOGFIRE_SERVICE_NAME=agentseek
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
```

`agentseek` and `bub` already call `logfire.configure()` during CLI bootstrap when `logfire` is installed, so this plugin only adds instrumentation patches and does not call `configure()` again.

## Run

Minimal local run with the agentseek entry point:

```bash
LOGFIRE_SEND_TO_LOGFIRE=false \
LOGFIRE_SERVICE_NAME=agentseek \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces \
uv run --extra observability agentseek run "List your tools briefly."
```

The same package also works with upstream Bub:

```bash
LOGFIRE_SEND_TO_LOGFIRE=false \
LOGFIRE_SERVICE_NAME=bub \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces \
uv run --extra observability bub run "Summarize the last turn."
```

## Runtime Behavior

- The plugin applies idempotent monkey patches once when the Bub plugin is loaded.
- `any_llm.py` owns only any-llm spans such as provider creation, completions, responses, messages, and embeddings.
- `republic.py` owns only Republic spans such as chat execution, tool execution, tool calls, and tape recording.
- `bub.py` owns only Bub spans such as inbound turn handling and agent loop steps.
- Streaming responses keep their span open until the stream is fully consumed, instead of closing when the iterator is created.

## Verify

```bash
uv sync --extra observability
uv run python -m pytest contrib/agentseek-observability/tests
```

## Limitations

- This package depends on Logfire being installed and configured in the active runtime environment.
- It intentionally patches the shared runtime classes in place, so the spans appear for the whole process after the plugin is loaded.
- Provider-specific spans inside vendor SDKs still depend on their own instrumentation support; this package only covers the agentseek stack itself.
