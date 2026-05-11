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
| `AGENTSEEK_PROJECT` | Directory used by `agentseek install` as Bub's plugin sandbox. Defaults to `{AGENTSEEK_HOME}/agentseek-project`. Maps to `BUB_PROJECT`. |

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

When you use the bundled `docker compose` setup, the app stores tapes in `/workspace/.agentseek/agentseek-tapes.db` by default.

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

## Docker Workspace

These variables are primarily consumed by the Docker entrypoint and bundled compose workflow. The same entrypoint also respects the Bub aliases.

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_WORKSPACE_PATH` | Workspace root used by the container entrypoint. In the bundled compose setup it defaults to `/workspace`. |
| `AGENTSEEK_SKILLS_HOME` | Skills source directory used by the container entrypoint. By default it is `.agents/skills` under the workspace, and non-default values are linked back into the workspace path Bub scans. |
| `AGENTSEEK_MCP_CONFIG_PATH` | MCP config source file used by the container entrypoint. In Docker / Compose this usually points at `/workspace/.agents/mcp.json`, then links into Bub's `${BUB_HOME}/mcp.json` default location. |

When they are not set explicitly, the entrypoint treats `/workspace` as the default workspace root, uses `/workspace/.agents/skills` as the project skill root, and auto-discovers MCP config from `/workspace/.agents/mcp.json`.

## Onboarding

```bash
uv run agentseek onboard
```

The command writes configuration under the active agentseek home, which defaults to `.agentseek/config.yml` in the current workspace.
