# agentseek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

A database-native Agent Harness, by the [OceanBase](https://en.oceanbase.com/) OSS Team.

## What agentseek is

agentseek is a database-native Agent Harness for teams that want agent runtime data to become a first-class database workload.

It treats the database as the natural place to keep agent context, execution history, tool calls, tasks, feedback, and observability together. The same runtime data can then serve debugging, replay, trajectory comparison, evaluation, analysis, and training workflows without being copied into separate systems or re-ingested later.

agentseek ships as two complementary packages on PyPI, split by job:

- **`agentseek-cli`** — the **project lifecycle CLI** (`create`, `run`, `build`, `deploy`, `api`, `ctx`, `skills`). Self-contained, installable with `uv tool install agentseek-cli`.
- **`agentseek`** — the **harness** itself. Provides the runtime CLI (`chat`, `run`, `gateway`, `install`, `update`, …) and the library you embed in your application. Resolved through this repository's `[tool.uv.sources]`, not via a direct `pip install agentseek`.

Both register a command named `agentseek`. See [`docs/index.md`](docs/index.md) and [`docs/explanation/choosing-an-entry-point.md`](docs/explanation/choosing-an-entry-point.md) for which one fits which job.

## Why it exists

Most agents already prove their value at runtime, but their runtime data is often scattered across JSONL logs, Markdown notes, SQLite files, tracing systems, object storage, and offline pipelines. After the first interaction, that data becomes expensive to query, replay, compare, evaluate, or turn into training material.

agentseek starts from a different assumption: context, memory, tasks, tool calls, traces, feedback, and evaluation material should share one durable substrate from the beginning. For agent systems, this makes runtime data reusable. For databases, it opens a direct path to carry intelligent-application workloads instead of only storing final business results.

## Quick Start

Pick one of the two paths. They are both first-class.

### Path A — install the project lifecycle CLI

Use this when you want to scaffold a project, build an image, or call lifecycle commands without checking the repo out.

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # the generated project resolves the full harness via its own [tool.uv.sources]
```

### Path B — clone the repo and run the harness

Use this when you want to drive the harness itself — `chat`, `gateway`, `install`, and the rest of the runtime CLI.

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help     # chat / run / gateway / install / update / …
```

Configure a model, then start a local chat:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> Note: `pip install agentseek` and `uv tool install agentseek` will fail to resolve, because the harness depends on `bub-feishu`, `bub-mcp`, and the workspace contrib packages, which are wired via `[tool.uv.sources]` and cannot be carried by PyPI metadata. Use one of the two paths above.

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
- [Tutorials](docs/tutorials/index.md): start here — quick CLI demo, first harness app, adding a skill and MCP.
- [How-to guides](docs/how-to/index.md): task-focused recipes for configuring models, installing plugins, running, and deploying.
- [Reference](docs/reference/index.md): environment variables, CLI commands, packages, file layout, templates, Docker.
- [Explanation](docs/explanation/index.md): what agentseek is, how it relates to Bub, runtime data model, extension model.
- [Blog intro](docs/blog/index.md): release notes, migrations, and longer-form posts.
- [Introducing agentseek](docs/blog/introducing-agentseek.md): lineage from bubseek, database-native harness, and Bub/tape store.

Contrib packages document their complete setup in their own README files:

- [agentseek-observability](contrib/agentseek-observability/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## How it works

- **Two packages, two paths** — `agentseek-cli` (project lifecycle CLI) and `agentseek` (harness). Same command name, different command surface. See [`docs/explanation/choosing-an-entry-point.md`](docs/explanation/choosing-an-entry-point.md).
- **Bub as the upstream runtime** — [Bub](https://github.com/bubbuild/bub) provides the hook-first turn pipeline, tape store, skills, plugins, and channel model that the harness runs on. agentseek consumes Bub as a library; it is not a re-skin.
- **`.agentseek` runtime home** — when the harness boots, it uses `.agentseek/` under the current workspace as runtime home, and `agentseek-project` as the plugin sandbox used by `agentseek install`. Override via env vars in [`docs/reference/environment.md`](docs/reference/environment.md).
- **Environment aliases** — `AGENTSEEK_*` values act as fallbacks for matching `BUB_*` values, so projects keep their own naming namespace while staying compatible with the upstream.
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
