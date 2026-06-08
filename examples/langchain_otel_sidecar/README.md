# LangChain OTEL + agentseek Sidecar

This is a **How-to Guide**. It shows how to keep a LangChain application as a normal business
service, export OpenTelemetry traces to Jaeger, and use an `agentseek` sidecar to analyze those
traces through `opentelemetry-mcp-server`.

## What You Will Get

When you finish, the topology looks like this:

```text
HTTP request
  -> langchain-app
    -> LangChain create_agent(...)
      -> OTLP HTTP exporter
        -> Jaeger
          -> opentelemetry-mcp-server
            -> agentseek sidecar
```

This example intentionally separates the trace-producing business process from the trace-analysis
agent process. That is usually a better match for real LangChain deployments than routing business
traffic through an agent harness.

## Files in This Example

| File | Purpose |
| --- | --- |
| [`app.py`](app.py) | Minimal FastAPI + LangChain application that produces OTEL traces. |
| [`settings.py`](settings.py) | Reads model and OTEL settings, and bridges OpenAI-compatible env vars. |
| [`requirements.txt`](requirements.txt) | Python dependencies for the business app. |
| [`Dockerfile.app`](Dockerfile.app) | Container image for the LangChain business app. |
| [`docker-compose.yml`](docker-compose.yml) | Topology for Jaeger, the LangChain app, and the agentseek sidecar. |
| [`.agents/mcp.json`](.agents/mcp.json) | Sidecar MCP config that launches `opentelemetry-mcp-server`. |
| [`AGENTS.md`](AGENTS.md) | Minimal sidecar instructions that bias analysis toward `mcp.otel_*` tools. |
| [`.env.example`](.env.example) | Environment template for the example. |

## Step 1: Prepare Environment Variables

From the repository root:

```bash
cp examples/langchain_otel_sidecar/.env.example examples/langchain_otel_sidecar/.env
```

Then edit `examples/langchain_otel_sidecar/.env` with a working OpenAI-compatible provider.

By default, this example reuses `AGENTSEEK_MODEL`, `AGENTSEEK_API_KEY`, and
`AGENTSEEK_API_BASE`, so the business app and the sidecar can share one model configuration. If
you want to split them, use `LANGCHAIN_OTEL_DEMO_*` for the business app instead.

## Step 2: Start Jaeger, the Business App, and the Sidecar

```bash
docker compose -f examples/langchain_otel_sidecar/docker-compose.yml up --build -d
```

After startup:

- Jaeger UI: `http://127.0.0.1:16686`
- LangChain demo app: `http://127.0.0.1:8080`
- agentseek sidecar: stays idle until you enter it with `docker compose exec`

## Step 3: Generate a Few Traces

Check that the app is healthy:

```bash
curl -s http://127.0.0.1:8080/healthz | python3 -m json.tool
```

Then send two different requests:

```bash
curl -s http://127.0.0.1:8080/invoke \
  -H 'content-type: application/json' \
  -d '{
    "prompt": "Plan a safe rollout for enabling a new read path behind a feature flag.",
    "session_id": "rollout-demo"
  }' | python3 -m json.tool
```

```bash
curl -s http://127.0.0.1:8080/invoke \
  -H 'content-type: application/json' \
  -d '{
    "prompt": "For the checkout service, list the top observability checks before a canary.",
    "session_id": "observability-demo"
  }' | python3 -m json.tool
```

Those requests should create traces under the `langchain-otel-demo` service in Jaeger, including
both FastAPI entry spans and LangChain/tool-related spans.

## Step 4: Use the agentseek Sidecar to Analyze the Traces

The simplest path is a one-shot `agentseek turn` inside the sidecar:

```bash
docker compose -f examples/langchain_otel_sidecar/docker-compose.yml exec agentseek-sidecar \
  uv run --no-sync --no-env-file agentseek turn \
  "Use your OpenTelemetry tools to inspect the latest traces from service langchain-otel-demo. Summarize the request flow, the slowest spans, tool usage, token usage, and any errors."
```

If you want an interactive session instead:

```bash
docker compose -f examples/langchain_otel_sidecar/docker-compose.yml exec agentseek-sidecar bash
uv run --no-sync --no-env-file agentseek chat
```

Then ask something like:

```text
Use mcp.otel_list_services first, then inspect the newest traces for langchain-otel-demo.
Tell me which request was slowest, whether any tool call dominated latency,
and whether the token usage looks abnormal.
```

## Why This Example Uses a Sidecar

Two reasons matter:

1. Most LangChain applications are business services first, not agent harnesses.
2. A sidecar fits the common production pattern better: the business process emits OTEL data, and a
   separate analysis process consumes it on demand.

In short, this example demonstrates:

```text
instrument once, analyze later
```

instead of:

```text
route every business request through agentseek
```

## Verify

Useful checks:

```bash
python3 -m json.tool examples/langchain_otel_sidecar/.agents/mcp.json >/dev/null
python3 -m compileall examples/langchain_otel_sidecar
docker compose -f examples/langchain_otel_sidecar/docker-compose.yml ps
```

At runtime, verify that:

- Jaeger shows the `langchain-otel-demo` service.
- `agentseek turn` can call `mcp.otel_*` tools.
- The sidecar answer can describe trace structure, latency hotspots, and any failures.

## Cleanup

```bash
docker compose -f examples/langchain_otel_sidecar/docker-compose.yml down --volumes
rm -rf examples/langchain_otel_sidecar/.agentseek
```

## When Not to Use This Example

This example is not the right fit when:

- you want `agentseek` to directly host the LangChain runnable;
- you need the AG-UI / CopilotKit frontend layer;
- you do not want Jaeger or another OTLP backend at all.

Related examples:

- agentseek-api remote agent: [`../agentseek_api_remote_agent/README.md`](../agentseek_api_remote_agent/README.md)
