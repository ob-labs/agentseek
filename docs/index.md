---
hide_sidebar: true
---

# agentseek

A database-native Agent Harness, by the OceanBase OSS Team.

agentseek is a database-native Agent Harness for teams that want agent runtime
data to become a first-class database workload.

It treats the database as the natural place to keep agent context, execution
history, tool calls, tasks, feedback, and observability together. The same
runtime data can then serve debugging, replay, trajectory comparison,
evaluation, analysis, and training workflows without being copied into separate
systems or re-ingested later.

## Two packages, two paths

agentseek ships as two complementary packages on PyPI, split by job:

- **`agentseek-cli`** — the project lifecycle CLI: `create`, `run`, `build`,
  `deploy`, `api`, `ctx`, `skills`. Self-contained, installable with
  `uv tool install agentseek-cli`.
- **`agentseek`** — the harness itself: `chat`, `run`, `gateway`, `install`,
  `update`, and the library surface you embed in your application. Resolved
  through this repository's `[tool.uv.sources]`, not through a direct
  `pip install agentseek`.

Both register a command named `agentseek`. See
[Choosing an entry point](explanation/choosing-an-entry-point.md) for which one
fits which job.

## Why it exists

Most agents prove their value at runtime, but their runtime data quickly
scatters across logs, notes, local databases, tracing systems, object storage,
and offline pipelines. After the first interaction, that makes replay,
comparison, evaluation, and training materially more expensive.

agentseek starts from the opposite assumption: context, memory, tasks, tool
calls, traces, feedback, and evaluation material should share one durable
substrate from the beginning.

For agent systems, this makes runtime data reusable. For databases, it opens a
direct path to carry intelligent-application workloads instead of only storing
final business results.

## Quick Start

Pick one of the two paths. They are both first-class.

### Path A — install the project lifecycle CLI

Use this when you want to scaffold a project, build an image, or call lifecycle
commands without checking the repository out.

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # the generated project resolves the full harness via its own [tool.uv.sources]
```

### Path B — clone the repo and run the harness

Use this when you want to drive the harness itself — `chat`, `gateway`,
`install`, and the rest of the runtime CLI.

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

Configure a model, then start a local session:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> Note: `pip install agentseek` and `uv tool install agentseek` will fail to
> resolve, because the harness depends on `bub-feishu`, `bub-mcp`, and the
> workspace contrib packages wired via `[tool.uv.sources]`. Use one of the two
> paths above.

## Read next

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">Documentation</a></h3>
    <p>What agentseek is, where it fits, and how the documentation is structured.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/">Tutorials</a></h3>
    <p>Start here: quick CLI demo, first harness app, and adding a skill and MCP.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">How-to guides</a></h3>
    <p>Task-focused recipes for configuring models, installing plugins, running, and deploying.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">Reference</a></h3>
    <p>Environment variables, CLI commands, packages, file layout, templates, and Docker.</p>
  </div>
</div>
