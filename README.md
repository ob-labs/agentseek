# agentseek

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

A database-native Agent Harness, by the [OceanBase](https://en.oceanbase.com/) OSS Team.

## Quick Start

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

Configure model and database, then verify:

```bash
export BUB_MODEL=openrouter:qwen/qwen3-coder-next
export BUB_API_KEY=sk-or-v1-your-key
export BUB_API_BASE=https://openrouter.ai/api/v1
export BUB_TAPESTORE_SQLALCHEMY_URL=mysql+oceanbase://user:pass@host:port/database
uv run agentseek chat
```

See [Getting started](docs/getting-started.md) for detailed setup guide.

## What is agentseek

agentseek is a database-native Agent Harness for teams that want agent runtime data to become a first-class database workload.

It treats the database as the natural place to keep agent context, execution history, tool calls, tasks, feedback, and observability together. The same runtime data can then serve debugging, replay, trajectory comparison, evaluation, analysis, and training workflows without being copied into separate systems or re-ingested later.

## Why agentseek

Most agents already prove their value at runtime, but their runtime data is often scattered across JSONL logs, Markdown notes, SQLite files, tracing systems, object storage, and offline pipelines. After the first interaction, that data becomes expensive to query, replay, compare, evaluate, or turn into training material.

agentseek starts from a different assumption: context, memory, tasks, tool calls, traces, feedback, and evaluation material should share one durable substrate from the beginning. For agent systems, this makes runtime data reusable. For databases, it opens a direct path to carry intelligent-application workloads instead of only storing final business results.

## How it works

- **Bub as the runtime layer** — [Bub](https://github.com/bubbuild/bub) provides the CLI, hook-first turn pipeline, tape context, skills, plugins, and channel model. agentseek uses Bub as the default governance layer, not as the product boundary.
- **Database-backed runtime storage** — SQLAlchemy-backed tape storage keeps runtime records in a database instead of a file-heavy context stack.
- **Open authoring model** — `AGENTS.md` and Agent Skills are first-class parts of the authoring and extension workflow.
- **Team chat entry points** — Telegram comes from Bub, Feishu ships with agentseek, and other channels stay opt-in through contrib packages.
- **Queryable footprint** — Tape-backed sessions, tasks, and traces can be inspected directly in the database and reused by downstream analysis workflows.

agentseek is database-neutral. SQLite or any suitable SQLAlchemy backend can be used where it fits. For a good default experience from local development to larger deployments, we recommend [OceanBase seekdb](https://github.com/oceanbase/seekdb) and OceanBase.

## Learn more

- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## License

[Apache-2.0](LICENSE)
