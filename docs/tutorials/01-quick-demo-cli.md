---
title: 01 — Quick demo via the CLI
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.md
---

# Quick demo via the CLI

You will run AgentSeek as a CLI tool, configure a model, and start one local
chat session.

## 1. Install the CLI

```bash
uv tool install agentseek
```

Confirm the CLI loads:

```bash
agentseek --help
```

If the help page prints, the tool is ready.

## 2. Configure a model

Create a small working directory and add model variables:

```bash
mkdir agentseek-demo
cd agentseek-demo
cat > .env <<'EOF'
AGENTSEEK_MODEL=openrouter:free
AGENTSEEK_API_KEY=sk-or-v1-replace-me
AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
EOF
```

Replace the API key with a real key before you expect model output.

## 3. Run one chat

```bash
agentseek chat
```

Type a short prompt at the `agentseek >` prompt. Exit with `Ctrl-D`.

For a single prompt without entering the chat loop:

```bash
agentseek turn "summarize this workspace in one sentence"
```

## What you have now

- AgentSeek installed as a CLI tool.
- Model settings in `.env`.
- A local runtime path through `agentseek chat` or `agentseek turn`.

## Next

- Create an editable project: [First harness app](02-first-harness-app.md).
- Look up exact flags: [CLI reference](../reference/cli.md).
