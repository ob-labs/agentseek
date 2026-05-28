---
title: How to configure MCP servers
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# How to configure MCP servers

Use this when you want the agent to call external tools or services exposed
over MCP. agentseek consumes MCP configuration through `bub-mcp`, which reads
the file at `${BUB_MCP_CONFIG_PATH}` (default: `${BUB_HOME}/mcp.json`).

## Prerequisites

- agentseek installed (`bub-mcp` is a core dependency, `pyproject.toml:21`).
- At least one MCP server you want to register.

## Choose a location

| You want to… | Put `mcp.json` here | Variable to set |
| --- | --- | --- |
| Keep MCP next to Bub runtime state (default) | `.agentseek/mcp.json` | none (default) |
| Co-locate with your project's `.agents/` skills folder | `.agents/mcp.json` | `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json` |
| Use a custom location | anywhere | `AGENTSEEK_MCP_CONFIG_PATH=<path>` |

In Docker, the entrypoint auto-discovers `${workspace}/.agents/mcp.json` and
symlinks it into `${AGENTSEEK_HOME}/mcp.json` (`entrypoint.sh:13`, `:37`).

## Steps

1. Write the MCP server file. See `add-mcp-server.md` for the entry format.

   ```json title=".agentseek/mcp.json"
   {
     "mcpServers": {
       "echo": {
         "command": "uvx",
         "args": ["mcp-server-echo"]
       }
     }
   }
   ```

2. If you chose a non-default location, set the path:

   ```bash title=".env"
   AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
   ```

3. Verify the file is picked up by running a chat session.

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

   TODO(reviewer): confirm MCP wiring with a real server when a credential is
   available. `--help` succeeded in this run.

### CLI shortcut

There is no dedicated `agentseek mcp` subcommand. Configuration is purely by
file path + environment variable.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| MCP servers do not appear in `tools/list` | `mcp.json` is at a path Bub does not read | Set `AGENTSEEK_MCP_CONFIG_PATH` to the file's path. |
| Edits to `mcp.json` are not reflected | Process was started before the edit | Restart `agentseek chat` / `agentseek gateway`. |

## Rollback

Delete the `mcp.json` file. Unset `AGENTSEEK_MCP_CONFIG_PATH` if you set it.

## Related

- How-to: `add-mcp-server.md`, `configure-docker-workspace.md`
- Reference: `../reference/environment.md`, `../reference/docker.md`
