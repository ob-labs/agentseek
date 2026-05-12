# agentseek

agentseek is a database-native Agent Harness. It packages Bub with agentseek defaults, `AGENTSEEK_*` configuration aliases, and a project-local runtime layout.

This page explains the project boundary and how to choose the right document. If you want to run the project first, start with [Getting started](getting-started.md).

## What It Is

agentseek treats runtime data as database data. Context, tasks, tool calls, traces, feedback, and conversation history should live in a durable substrate rather than scattered files and side-channel logs.

At the runtime layer, agentseek follows Bub's hook, channel, tape, skill, and plugin model. The agentseek layer adds:

- the `agentseek` CLI entry point
- project-local defaults such as `.agentseek`
- `AGENTSEEK_*` aliases for Bub-compatible settings
- branded onboarding and plugin sandbox defaults
- bundled release skills under `src/skills`

Database storage, LangChain routing, persistent scheduling, and other larger integrations are documented by their contrib packages instead of this main docs set.

## What It Is Not

agentseek is not a replacement for Bub. It follows Bub's runtime and extension model, and `bub` remains available when you want to use the upstream CLI or extension namespace directly.

agentseek is also not a single-purpose chat bot or a model provider wrapper. The project boundary is the harness: defaults, packaging, runtime home, environment aliases, bundled skills, and a small branded entry point.

## Documentation Map

The docs follow the Diataxis split between learning, reference, how-to guidance, and explanation:

- [Getting started](getting-started.md) is a tutorial. Use it when you want a working local or Docker Compose run.
- [Configuration](configuration.md) is a reference. Use it when you need exact agentseek alias, path, and Docker defaults.
- [Extensions](extensions.md) is a how-to guide. Use it when you need to add instructions, skills, MCP config, or Bub-compatible plugins.
- This page is the explanation layer. Use it to understand what agentseek owns and what remains Bub behavior.

## Runtime Shape

A typical local run looks like this:

```text
workspace/
  .agentseek/                 runtime home, config.yml, default MCP config
  .agents/
    skills/                   project-local skills discovered by Bub
    mcp.json                  optional project-level MCP config
```

In Docker Compose, the repository or selected host workspace is mounted at `/workspace`. The entrypoint sets `BUB_HOME` from `AGENTSEEK_HOME`, links project skills into `.agents/skills` when needed, links `.agents/mcp.json` into the runtime MCP path when present, and starts `agentseek gateway` unless the workspace provides an optional `startup.sh`.

## Contrib Scope

Contrib packages keep their full setup and usage references in their own README files:

- [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase): SQLAlchemy tape storage, OceanBase compatibility, and optional vector retrieval.
- [agentseek-langchain](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain): routing Bub model calls through a LangChain `Runnable`.
- [agentseek-schedule-sqlalchemy](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-schedule-sqlalchemy): SQLAlchemy-backed APScheduler persistence.

The main docs link to contrib packages but do not duplicate their configuration tables.
