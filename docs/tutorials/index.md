---
title: Tutorials
type: tutorial
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - templates/index.json
  - README.md
  - docs/index.md
---

# Tutorials

Tutorials are learning-oriented walk-throughs. Each one starts from a clean state, runs end
to end, and leaves you with a concrete artefact you can keep. Pick the page that matches
your goal; do not skim across all three at once.

agentseek ships as two complementary packages split by job. `agentseek-cli` owns the
project lifecycle commands (`create / run / build / deploy / api / ctx / skills`);
`agentseek` is the harness itself (runtime CLI plus the library you embed). The tutorials
below cover both paths: tutorial 01 runs the harness directly from a synced checkout;
tutorial 02 starts with the lifecycle CLI and lands inside a generated harness project.

If you want a task recipe instead (cookbook style), see the
[How-to guides](../how-to/index.md). For exact flag names or environment aliases,
see the [Reference](../reference/index.md).

## Audience matrix

| If you are… | Start with | Then |
| --- | --- | --- |
| A1 — a first-time evaluator | [Quick demo (CLI)](01-quick-demo-cli.md) | [What agentseek is](../explanation/what-agentseek-is.md) |
| A2 — building an app on top of agentseek | [First harness app](02-first-harness-app.md) | [Add a skill and MCP](03-add-a-skill-and-mcp.md), then [How-to guides](../how-to/index.md) |
| A3 — writing a plugin or integration | [First harness app](02-first-harness-app.md) | [Runtime data model](../explanation/runtime-data-model.md), then [Author a contrib plugin](../how-to/author-a-contrib-plugin.md) |
| A4 — operating a deployment | [Add a skill and MCP](03-add-a-skill-and-mcp.md) | [Run with Docker Compose](../how-to/run-with-docker-compose.md), then [Environment variables](../reference/environment.md) |
| A5 — just curious | skip tutorials | [What agentseek is](../explanation/what-agentseek-is.md) |

## The three tutorials

1. **[Quick demo (CLI)](01-quick-demo-cli.md).** A five-minute evaluator path:
   clone, `uv sync`, set three environment variables, run `agentseek chat`. This is
   **Path B** from the overview: the harness runtime CLI from a synced checkout. Use it
   when you are evaluating agentseek, running a local one-off workflow, or poking at the
   runtime to diagnose something.
2. **[First harness app](02-first-harness-app.md).** The application-developer path.
   Start with `agentseek create` (owned by `agentseek-cli`), then `uv sync` inside the
   generated project so the harness itself resolves there. After this page, that generated
   project — not the cloned repo — is the surface you keep editing.
3. **[Add a skill and MCP](03-add-a-skill-and-mcp.md).** Operational shape:
   drop a project-local skill under `.agents/skills/<name>/SKILL.md`, register an MCP
   server in `.agents/mcp.json` (or `.agentseek/mcp.json`), and watch the running agent
   pick both up.

## Ground rules

- The tutorials assume Python 3.12+, [uv](https://docs.astral.sh/uv/), and a Unix-like
  shell. Windows works through WSL2.
- Every command runs verbatim from the repository root unless the tutorial says
  otherwise. If a command fails for you, fix the failure before moving on — later steps
  assume the previous one succeeded.
- API keys in examples are obvious placeholders (`sk-or-v1-…`). Replace them with real
  values before you expect real model output.
- These pages are validated against the live repository on the date in the front-matter.
  If the date is stale, file an issue rather than guessing.
