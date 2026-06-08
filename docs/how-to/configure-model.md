---
title: How to configure the model provider
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - README.md
  - docs/index.md
---

# How to configure the model provider

Use this when you need to point agentseek at a specific LLM (OpenRouter,
OpenAI, an OpenAI-compatible gateway, a local server, …). agentseek does not
ship default credentials; you must set the model and a key before any chat
turn can run.

## Prerequisites

- A working AgentSeek environment: either this repository after `uv sync`,
  a generated project after its own `uv sync`, or an installed `agentseek` tool.
- A valid API key for your chosen provider.

## Steps

1. Pick a model identifier accepted by Bub's any-llm layer. Common forms:
   `openrouter:<model>`, `openai:gpt-4o-mini`, `openai:<model>@<base_url>`.

2. Put the configuration in `.env` at your project root. agentseek loads
   `.env` from the current working directory (`src/agentseek/env.py:38`).

   ```bash title=".env"
   AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free
   AGENTSEEK_API_KEY=sk-or-v1-replace-me   # fake placeholder
   # Optional — only when your provider is not the model's default endpoint
   # AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
   ```

   `AGENTSEEK_*` aliases to `BUB_*` at startup (`src/agentseek/env.py:56`).
   If `BUB_*` is already set in the process env, it wins — useful for
   one-off overrides.

3. Verify the alias mapping landed by inspecting the resolved help (this
   reads `.env`):

   ```bash
   uv run agentseek chat --help
   ```

   ```text title="output"
   Usage: agentseek chat [OPTIONS]
   ```

   No traceback means `.env` parsed cleanly.

### CLI shortcut

To override per invocation without editing `.env`:

```bash title="not executed in this run"
AGENTSEEK_MODEL=openai:gpt-4o-mini \
AGENTSEEK_API_KEY=sk-replace-me \
uv run agentseek chat
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` from provider | `AGENTSEEK_API_KEY` missing or stale | Re-issue the key and update `.env`; restart the process. |
| Calls hit the wrong endpoint | `AGENTSEEK_API_BASE` not set for an OpenAI-compatible gateway | Set `AGENTSEEK_API_BASE` to the gateway's `…/v1` URL. |
| Setting is ignored | Same variable is set as `BUB_*` in your shell | `BUB_*` wins by `setdefault` — unset it or update it. |

## Rollback

Delete the lines from `.env`, or `unset AGENTSEEK_MODEL AGENTSEEK_API_KEY` in
your shell. There is no on-disk state to clean up.

## Related

- Reference: [Environment variables reference](../reference/environment.md)
- Explanation: [How agentseek relates to Bub](../explanation/bub-relationship.md)
