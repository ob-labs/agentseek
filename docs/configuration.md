# Configuration

This is a reference for the built-in agentseek configuration layer. For a guided setup, use [Getting started](getting-started.md).

The examples use `AGENTSEEK_*` names because they are the project-facing names for this distribution. Bub-compatible `BUB_*` names remain valid.

Contrib packages keep their own configuration references in their README files.

## Environment Naming

agentseek accepts both `AGENTSEEK_*` and `BUB_*`.

Prefer `AGENTSEEK_*` in agentseek projects. At startup, agentseek maps missing `BUB_*` values from matching `AGENTSEEK_*` values. If both are set, `BUB_*` takes precedence.

agentseek also reads `.env` in the current working directory. Process environment values override `.env` values for the same setting.

## Default Layout

When no home or project path is set, agentseek uses the current workspace:

```text
.agentseek/
  config.yml
  mcp.json
  agentseek-project/
```

`agentseek install ...` uses `agentseek-project` as the default plugin sandbox. Set `AGENTSEEK_PROJECT` or `BUB_PROJECT` to use another sandbox directory.

## Common Runtime Aliases

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MODEL` | Model identifier, such as `openrouter:free`. |
| `AGENTSEEK_API_KEY` | API key for the configured model provider. |
| `AGENTSEEK_API_BASE` | OpenAI-compatible API base URL. |
| `AGENTSEEK_HOME` | Runtime home. Defaults to `.agentseek` in the current workspace. |
| `AGENTSEEK_PROJECT` | Directory used by `agentseek install` as Bub's plugin sandbox. Defaults to `{AGENTSEEK_HOME}/agentseek-project`. Maps to `BUB_PROJECT`. |

## Optional Runtime Variables

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MAX_STEPS` | Maximum model/tool loop steps. |
| `AGENTSEEK_MAX_TOKENS` | Response token budget. |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | Model request timeout. |

## MCP

`bub-mcp` reads MCP server definitions from `${BUB_HOME}/mcp.json` by default. With agentseek defaults, that means `.agentseek/mcp.json` in the current workspace.

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MCP_CONFIG_PATH` | Alias for Bub's MCP config path. Use it when you want MCP config somewhere other than `${AGENTSEEK_HOME}/mcp.json`, such as `.agents/mcp.json` in the project root. |

In Docker / Compose, the entrypoint adds one convenience layer on top: if `.agents/mcp.json` exists in the mounted workspace, it links that file into the runtime MCP config path automatically.

## Docker Workspace

These variables are primarily consumed by the Docker entrypoint and bundled compose workflow. The same entrypoint also respects the Bub aliases.

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | Host path mounted by Docker Compose into `/workspace`. Defaults to the repository root. |
| `AGENTSEEK_WORKSPACE_PATH` | Workspace root used by the container entrypoint. In the bundled compose setup it defaults to `/workspace`. |
| `AGENTSEEK_HOME` | Runtime home inside the container. Defaults to `/workspace/.agentseek` in the bundled compose setup. |
| `AGENTSEEK_PROJECT` | Plugin sandbox inside the container. Defaults to `/workspace/.agentseek/agentseek-project` in the bundled compose setup. |
| `AGENTSEEK_SKILLS_HOME` | Skills source directory used by the container entrypoint. By default it is `.agents/skills` under the workspace, and non-default values are linked back into the workspace path Bub scans. |
| `AGENTSEEK_MCP_CONFIG_PATH` | MCP config source path. Compose sets it to `/workspace/.agents/mcp.json` by default. |

When they are not set explicitly, the entrypoint treats `/workspace` as the default workspace root and uses `/workspace/.agents/skills` as the project skill root.

If `/workspace/startup.sh` exists, the entrypoint runs it. Otherwise it starts `agentseek gateway`.

## Onboarding

```bash
uv run agentseek onboard
```

The command writes configuration under the active agentseek home, which defaults to `.agentseek/config.yml` in the current workspace.

Installed Bub plugins can contribute onboarding prompts and write their own config sections.

## Contrib Configuration

Configuration for contrib integrations is documented with each package:

- [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase): SQLAlchemy tape storage, OceanBase URL compatibility, and vector settings.
- [agentseek-langchain](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain): LangChain factory, tool bridging, and tape recording settings.
- [agentseek-schedule-sqlalchemy](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-schedule-sqlalchemy): scheduler database URL, table name, and fallback behavior.
