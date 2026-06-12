---
title: How to configure the model provider
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - README.md
  - docs/index.md
---

# How to configure the model provider

Use this when AgentSeek should call your model provider.

## Prerequisites

- A working AgentSeek environment.
- A valid API key for your chosen provider.

## Steps

1. Create or edit `.env` in the directory where you run AgentSeek.

   ```bash title=".env"
   AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free
   AGENTSEEK_API_KEY=sk-or-v1-replace-me   # fake placeholder
   ```

2. Add a base URL only for an OpenAI-compatible endpoint.

   ```bash title=".env"
   AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
   ```

3. Start a chat from the same directory.

   ```bash
   agentseek chat
   ```

AgentSeek also accepts the matching `BUB_*` variables. If both prefixes are
present, `BUB_*` wins.

### CLI shortcut

Use process environment variables for a one-off run:

```bash
AGENTSEEK_MODEL=openai:gpt-4o-mini \
AGENTSEEK_API_KEY=sk-replace-me \
agentseek chat
```

The key shown here is a placeholder.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` | The key is missing or expired. | Update `AGENTSEEK_API_KEY`. |
| Requests reach the wrong endpoint | The provider needs a custom base URL. | Set `AGENTSEEK_API_BASE`. |
| `.env` value is ignored | The same `BUB_*` variable exists in your shell. | Unset the shell variable or update it. |

## Rollback

Remove the model lines from `.env`, or unset the same variables in your shell.

## Related

- Reference: [Environment variables reference](../reference/environment.md)
- Explanation: [How agentseek relates to Bub](../explanation/bub-relationship.md)
