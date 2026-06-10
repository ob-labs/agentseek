---
title: 01 — Quick demo via the CLI
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.md
---

# Quick demo via the CLI

You will clone the repository, install dependencies, configure a model, and run
one chat session through `agentseek chat`.

## 1. Clone and install

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
```

Verify the CLI is available:

```bash
uv run agentseek --help
```

You should see commands for project management (`create`, `run`, `build`,
`deploy`), runtime (`chat`, `turn`, `gateway`), and extensions (`plugin`,
`ctx`, `skills`, `api`).

## 2. Point AgentSeek at a model

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-replace-me
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

Replace the API key with a real key before expecting model output. You can also
copy `.env.example` to `.env` and edit the file instead:

```bash
cp .env.example .env
```

## 3. Start chat

```bash
uv run agentseek chat
```

Type a short prompt at the `agentseek >` prompt. Exit with `Ctrl+D` or the
configured quit command.

For a single prompt without entering the REPL:

```bash
uv run agentseek turn "summarize this workspace in one sentence"
```

## What you have now

- A synced repository environment.
- Model configuration through `AGENTSEEK_*` variables or `.env`.
- A working `agentseek chat` or `agentseek turn` setup.

## Next

- Build an application project: [First harness app](02-first-harness-app.md).
- Explore available commands: [CLI reference](../reference/cli.md).
