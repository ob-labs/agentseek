---
title: Observability and Tracing
type: how-to
audience: [A2, A4]
runs: no
verified_on: 2026-06-27
sources:
  - src/agentseek/env.py
  - src/agentseek/__main__.py
  - templates/langchain/default/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/default/{{cookiecutter.project_slug}}/README.md
  - templates/langchain/default/{{cookiecutter.project_slug}}/docker-compose.yml
  - templates/deepagents/research/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/sandbox/{{cookiecutter.project_slug}}/.env.example
---

# Observability and Tracing

Use this guide when local runs work, but traces or diagnostic output are not
showing up where you expect them.

## Choose The Trace Target

| Target | Use when | Configuration surface |
| --- | --- | --- |
| LangSmith cloud | You want hosted LangChain or LangGraph traces. | `LANGSMITH_*` variables in `.env` or the shell. |
| AgentSeek console | You want local CLI diagnostic spans and events. | `AGENTSEEK_CONSOLE=true`. |
| Phoenix | You use `langchain/default` and want local OpenTelemetry traces. | `AGENTSEEK_OTEL_*` variables and the template compose stack. |

These targets are independent. Enabling one does not send data to the others.

## Configure LangSmith Cloud Tracing

Set the LangSmith variables used by LangChain and LangGraph templates.

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=<your-project-name>
```

Use `LANGSMITH_ENDPOINT` when your API key belongs to a non-default region.
For APAC keys, configure the APAC endpoint.

```env
LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com
```

The LangSmith observability quickstart documents the same regional endpoint
behavior: non-US regions need `LANGSMITH_ENDPOINT`, or the API key may not
authenticate against the default endpoint.

See the report in
[ob-labs/agentseek#83](https://github.com/ob-labs/agentseek/issues/83) for the
APAC failure mode that motivated this guide.

## Diagnose Local Studio Without Cloud Traces

Local Studio or a local thread page can show runs from your local development
server even when cloud trace ingestion is failing.

Use this checklist when Studio is visible but LangSmith cloud traces are
missing.

| Check | What to fix |
| --- | --- |
| `LANGSMITH_TRACING` is not `true` | Enable tracing in the same environment that starts the app. |
| `LANGSMITH_API_KEY` is empty or from another region | Use a key from the target LangSmith region. |
| `LANGSMITH_ENDPOINT` is missing for APAC or another non-default region | Set the regional endpoint explicitly. |
| `LANGSMITH_PROJECT` is different from the dashboard project you opened | Open the configured project or change the variable. |
| The app process does not load `.env` | Export the variables in the shell that starts the app. |

Treat local Studio visibility as a local runtime signal. Treat cloud traces as
a separate ingestion signal.

## Enable AgentSeek Console Output

Set `AGENTSEEK_CONSOLE=true` when you want AgentSeek CLI spans and events
rendered locally through Logfire console output.

```env
AGENTSEEK_CONSOLE=true
```

AgentSeek configures Logfire with `send_to_logfire=False`, so this does not
upload data to Logfire cloud. It only changes local console rendering for the
AgentSeek CLI process.

## Use Phoenix In `langchain/default`

The `langchain/default` template includes local OpenTelemetry export to
Phoenix. The generated app registers tracing in the LangChain application
process. Bub and the gateway only forward messages.

The compose stack sends spans to Phoenix from inside the app container.

```env
AGENTSEEK_OTEL_ENABLED=true
AGENTSEEK_OTEL_SERVICE_NAME=<project-slug>
AGENTSEEK_OTEL_PROJECT_NAME=<project-slug>
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://phoenix:6006/v1/traces
```

For non-compose runs, point the endpoint at localhost instead.

```env
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:6006/v1/traces
```

The template compose stack uses `ghcr.io/psiace/phoenix:mysql` for Phoenix and
persists Phoenix data through `quay.io/oceanbase/seekdb:latest`.

## Related

- [Lifecycle Spec reference](../reference/lifecycle-spec.md)
- [Templates reference](../reference/templates.md)
- [Run Local Development](run-local-development.md)
- [LangSmith observability quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
