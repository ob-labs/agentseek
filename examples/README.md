# agentseek Examples

This directory contains runnable examples for the repository-level `agentseek` distribution and
its contrib packages.

## Available Examples

| Example | Purpose |
| --- | --- |
| [`agentseek_api_remote_agent`](agentseek_api_remote_agent/README.md) | How to connect an `agentseek-api` remote agent to **`agentseek-langchain`** through `LangGraphClientRunnable`. |
| [`langchain_otel_sidecar`](langchain_otel_sidecar/README.md) | LangChain business app exports OTEL traces to Jaeger, while an **agentseek sidecar** analyzes them through `opentelemetry-mcp-server`. |

Examples are intentionally kept outside package source trees so they can show how the pieces are
installed and run together from a user workspace.
