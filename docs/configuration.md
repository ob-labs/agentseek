# Configuration

This is a reference for agentseek configuration. For a guided setup, use [Getting started](getting-started.md).

## Environment Naming

agentseek accepts both `AGENTSEEK_*` and `BUB_*`.

Prefer `AGENTSEEK_*` in agentseek projects. At startup, agentseek maps missing `BUB_*` values from matching `AGENTSEEK_*` values. If both are set, `BUB_*` takes precedence.

## Core Variables

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MODEL` | Model identifier, such as `openrouter:free`. |
| `AGENTSEEK_API_KEY` | API key for the configured model provider. |
| `AGENTSEEK_API_BASE` | OpenAI-compatible API base URL. |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | SQLAlchemy URL for runtime tape storage. |
| `AGENTSEEK_HOME` | Runtime home. Defaults to `.agentseek` in the current workspace. |

## Optional Runtime Variables

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MAX_STEPS` | Maximum model/tool loop steps. |
| `AGENTSEEK_MAX_TOKENS` | Response token budget. |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | Model request timeout. |

## Storage

agentseek uses SQLAlchemy-backed tape storage through `bub-tapestore-sqlalchemy`.

For local development:

```bash
AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-tapes.db
```

For deployment, use any suitable SQLAlchemy URL. OceanBase seekdb and OceanBase are recommended for a good local-to-cloud experience, but they are not required.

## Channels

Telegram is available through Bub. Feishu is bundled with agentseek.

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_TELEGRAM_TOKEN` | Telegram bot token. |
| `AGENTSEEK_TELEGRAM_ALLOW_USERS` | Optional Telegram user allowlist. |
| `AGENTSEEK_TELEGRAM_ALLOW_CHATS` | Optional Telegram chat allowlist. |
| `AGENTSEEK_FEISHU_APP_ID` | Feishu app ID. |
| `AGENTSEEK_FEISHU_APP_SECRET` | Feishu app secret. |
| `AGENTSEEK_FEISHU_VERIFICATION_TOKEN` | Optional Feishu verification token. |
| `AGENTSEEK_FEISHU_ENCRYPT_KEY` | Optional Feishu encrypt key. |

Other channels can be added through Bub-compatible plugins.

## Onboarding

```bash
uv run agentseek onboard
```

The command writes configuration under the active agentseek home, which defaults to `.agentseek/config.yml` in the current workspace.
