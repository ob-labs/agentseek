# agentseek

agentseek is a database-native Agent Harness. It packages Bub with database-backed runtime storage and a small set of defaults for teams that want agent runtime data to be queryable from the beginning.

This overview explains what agentseek is and how the documentation is organized. If you want to run it first, start with [Getting started](getting-started.md).

## What It Is

agentseek treats runtime data as database data: context, tasks, tool calls, traces, feedback, and conversation history should live in a durable substrate rather than scattered files and side-channel logs.

It remains database-neutral. SQLite is enough for local use, and any suitable SQLAlchemy backend can be used. For a smooth local-to-cloud path, we recommend OceanBase seekdb and OceanBase.

## What It Is Not

agentseek is not a replacement for Bub. It follows Bub's runtime and extension model, and `bub` remains available when you want to use the upstream CLI or extension namespace directly.

agentseek is also not a single-purpose chat bot. The project boundary is the harness: defaults, packaging, runtime storage, environment aliases, and a small branded entry point.

## Documentation Map

- [Getting started](getting-started.md): a short tutorial that gets agentseek running locally.
- [Configuration](configuration.md): a reference for environment variables, storage, channels, and onboarding.
- [Extensions](extensions.md): a guide to project instructions, plugins, and skills.
