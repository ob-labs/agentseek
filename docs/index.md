---
hide_sidebar: true
---

# agentseek

agentseek is a database-native Agent Harness for teams that want agent runtime
data to become a first-class database workload.

It keeps context, execution history, tool calls, tasks, feedback, and
observability on one durable database substrate.

## Quick Start

Pick one path: install `agentseek-cli` for project lifecycle commands, or clone
the repo and run `agentseek` for the harness CLI. For the trade-offs, see
[Choosing an entry point](explanation/choosing-an-entry-point.md).

### Path A — install the project lifecycle CLI

Use this to scaffold a project or run lifecycle commands without cloning the
repository.

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # the generated project resolves the full harness via its own [tool.uv.sources]
```

### Path B — clone the repo and run the harness

Use this to run the harness CLI itself: `chat`, `gateway`, `install`, and the
rest of the runtime surface.

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

Then configure a model and start a local session:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> Note: `pip install agentseek` and `uv tool install agentseek` will fail to
> resolve for the harness. Use one of the two paths above.

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
