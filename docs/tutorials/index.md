---
title: Tutorials
type: tutorial
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - templates/index.json
---

# Tutorials

Tutorials are learning-oriented walk-throughs. Each one starts from a clean state, runs end to
end, and leaves you with a concrete artefact you can keep. Pick the page that matches your
goal; do not skim across all three at once.

If you want a task recipe instead (cookbook style), see `../how-to/index.md`. If you want
exact flag names or environment aliases, see `../reference/index.md`.

## Audience matrix

| If you are… | Start with | Then |
| --- | --- | --- |
| A1 — a first-time evaluator | `01-quick-demo-cli.md` | `../explanation/what-agentseek-is.md` |
| A2 — building an app on top of agentseek | `02-first-harness-app.md` | `03-add-a-skill-and-mcp.md`, then `../how-to/` |
| A3 — writing a plugin or integration | `02-first-harness-app.md` (for the runtime shape) | `../explanation/runtime-data-model.md`, `../how-to/author-a-contrib-plugin.md` |
| A4 — operating a deployment | `03-add-a-skill-and-mcp.md` | `../how-to/run-with-docker-compose.md`, `../reference/environment.md` |
| A5 — just curious | skip tutorials | `../explanation/what-agentseek-is.md` |

## The three tutorials

1. **`01-quick-demo-cli.md` — Quick demo via the CLI.** A five-minute evaluator path: clone,
   `uv sync`, set three environment variables, run `agentseek chat`. This page is the demo
   entry point. It is deliberately *not* the recommended way to use agentseek in a real
   project; that path lives in tutorial 02.
2. **`02-first-harness-app.md` — Your first harness app.** The main onboarding tutorial.
   Generate a project from a built-in template, sync dependencies, and run an agent that you
   own end to end. After this page the harness/library form is the surface you will spend
   most of your time in.
3. **`03-add-a-skill-and-mcp.md` — Add a skill and an MCP server.** Operational shape: drop a
   project-local skill under `.agents/skills/<name>/SKILL.md`, register an MCP server in
   `.agents/mcp.json` (or `.agentseek/mcp.json`), and watch the running agent pick both up.

## Ground rules

- The tutorials assume Python 3.12+, [uv](https://docs.astral.sh/uv/), and a Unix-like shell.
  Windows works through WSL2.
- Every command is executed verbatim from the repository root unless the tutorial says
  otherwise. If a command fails for you, fix the failure before moving on — later steps
  assume the previous one succeeded.
- API keys in examples are obvious placeholders (`sk-or-v1-…`). Replace them with real values
  before you expect real model output.
- These pages are validated against the live repository on the date in the front-matter. If
  the date is stale, file an issue rather than guessing.
