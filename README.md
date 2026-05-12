# agentseek

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

A database-native Agent Harness, by the [OceanBase](https://en.oceanbase.com/) OSS Team.

## What agentseek is

agentseek is a database-native Agent Harness for teams that want agent runtime data to become a first-class database workload.

It treats the database as the natural place to keep agent context, execution history, tool calls, tasks, feedback, and observability together. The same runtime data can then serve debugging, replay, trajectory comparison, evaluation, analysis, and training workflows without being copied into separate systems or re-ingested later.

agentseek packages [Bub](https://github.com/bubbuild/bub) with agentseek defaults, environment aliases, and a project-local runtime layout. Use `agentseek` when you want the Bub runtime model with a project-local `.agentseek` home and `AGENTSEEK_*` configuration.

## Why it exists

Most agents already prove their value at runtime, but their runtime data is often scattered across JSONL logs, Markdown notes, SQLite files, tracing systems, object storage, and offline pipelines. After the first interaction, that data becomes expensive to query, replay, compare, evaluate, or turn into training material.

agentseek starts from a different assumption: context, memory, tasks, tool calls, traces, feedback, and evaluation material should share one durable substrate from the beginning. For agent systems, this makes runtime data reusable. For databases, it opens a direct path to carry intelligent-application workloads instead of only storing final business results.

## Quick Start

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

Configure a model, then start a local chat:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

`agentseek` is a Bub-compatible distribution entry point. It defaults to `.agentseek` under the current workspace for local config and runtime home. You can also use `uv run bub ...` and Bub plugins directly when you want the upstream CLI or extension namespace.

Project-local skills under `.agents/skills` work in local runs because Bub discovers project skills from the workspace. For MCP, `bub-mcp` uses `${BUB_HOME}/mcp.json` by default, which becomes `.agentseek/mcp.json` with agentseek defaults; if you prefer `.agents/mcp.json` in the project root, set `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json`.

## Docker Compose

If you want to run `agentseek` in a container with the project workspace mounted in, use the bundled compose setup:

```bash
cp .env.example .env
make compose-up
```

By default, compose will:

- mount the current repository into `/workspace`
- reuse `.agents/skills` and `.agents/mcp.json`
- persist runtime state under `.agentseek` in the workspace

To mount a different host directory as the workspace, set `AGENTSEEK_DOCKER_WORKSPACE`. To override the MCP config source path in containers, set `AGENTSEEK_MCP_CONFIG_PATH`.

## Documentation

The main documentation describes the built-in agentseek distribution layer:

- [Overview](docs/index.md): what agentseek is, where it fits, and how the docs are structured.
- [Getting started](docs/getting-started.md): a tutorial for running agentseek locally or with Docker Compose.
- [Configuration](docs/configuration.md): reference for agentseek environment aliases, local runtime paths, and Docker defaults.
- [Extensions](docs/extensions.md): how to add project instructions, skills, MCP config, and Bub-compatible plugins.

Contrib packages document their complete setup in their own README files:

- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## How it works

- **Bub as the runtime layer** — [Bub](https://github.com/bubbuild/bub) provides the CLI, hook-first turn pipeline, tape context, skills, plugins, and channel model. agentseek uses Bub as the default governance layer, not as the product boundary.
- **Project-local defaults** — `.agentseek` is the default runtime home, and `agentseek-project` is the default plugin sandbox used by `agentseek install`.
- **Environment aliases** — `AGENTSEEK_*` values act as fallbacks for matching `BUB_*` values, so agentseek projects can use their own naming namespace while staying Bub-compatible.
- **Open authoring model** — `AGENTS.md`, project-local skills, bundled skills, and MCP config are first-class parts of the authoring and extension workflow.
- **Contrib extension path** — database storage, LangChain routing, persistent scheduling, and other larger integrations live under `contrib/` and keep their full usage docs there.

For a good default experience from local development to larger deployments, we recommend [OceanBase seekdb](https://github.com/oceanbase/seekdb) and OceanBase.

## Development

```bash
make install
make check
make test
make docs-test
```

Contrib package README files document their package-specific checks.

## License

[Apache-2.0](LICENSE)
