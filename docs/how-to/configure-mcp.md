---
title: How to configure MCP servers
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - pyproject.toml
---

# How to configure MCP servers

Use this when AgentSeek should call tools exposed by MCP servers.

## Prerequisites

- `bub-mcp` installed in the project environment.
- At least one MCP server you can run from the same environment.

```bash
uv add bub-mcp
```

## Steps

1. Create `.agents/mcp.json` in your project.

   ```json title=".agents/mcp.json"
   {
     "mcpServers": {
       "local-tools": {
         "command": "python",
         "args": ["-m", "my_package.mcp_server"],
         "env": {
           "LOG_LEVEL": "info"
         }
       },
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_fake_replace_me"
         }
       }
     }
   }
   ```

2. Point AgentSeek at that file.

   ```bash title=".env"
   AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
   ```

3. Restart the runtime.

   ```bash
   uv run agentseek chat
   ```

In Docker, the default compose setup already points at `/workspace/.agents/mcp.json`.

### CLI shortcut

When `bub-mcp` is installed in the current CLI environment, `agentseek mcp`
can edit the same config file.

```bash
uv run agentseek mcp list
```

```text title="output"
No MCP tools registered.
```

```bash
uv run agentseek mcp add github https://example.com/mcp \
  --transport http --header "Authorization: Bearer $TOKEN"
```

```bash
uv run agentseek mcp add local-tools --transport stdio \
  --env LOG_LEVEL=info -- python -m my_package.mcp_server
```

Create the parent directory before using `mcp add` with a custom path.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No such command 'mcp'` | `bub-mcp` is not installed. | Add `bub-mcp` to the project. |
| Tools are missing | The server command failed. | Run the server command outside AgentSeek. |
| Auth fails | A token is missing from `env`. | Add the credential under that server entry. |
| Edits are not reflected | The runtime started before the edit. | Restart `agentseek chat` or `agentseek gateway`. |

## Rollback

Remove the server entry from `mcp.json`. Unset `AGENTSEEK_MCP_CONFIG_PATH` if
you set it.

## Related

- Reference: [Environment variables](../reference/environment.md)
- Docker: [How to run with Docker Compose](run-with-docker-compose.md)
