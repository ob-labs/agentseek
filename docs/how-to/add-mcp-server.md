---
title: How to add an MCP server
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# How to add an MCP server

Use this when you need to expose an external tool or service to the agent
over MCP. This page covers **authoring an entry**; see
`configure-mcp.md` for choosing **where** the file lives.

## Prerequisites

- agentseek installed (`bub-mcp` is a core dep, `pyproject.toml:21`).
- The MCP server itself runnable on your machine (a binary, a `uvx`
  package, an `npx` package, …).

## Steps

1. Pick (or create) the `mcp.json` location. Default is
   `${BUB_HOME}/mcp.json`, which with agentseek defaults is
   `.agentseek/mcp.json`.

2. Add a server entry under `mcpServers`. The shape mirrors the standard MCP
   client config:

   ```json title=".agentseek/mcp.json"
   {
     "mcpServers": {
       "fs": {
         "command": "uvx",
         "args": ["mcp-server-filesystem", "--root", "/workspace"],
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

3. Restart any running `agentseek chat` / `agentseek gateway` so `bub-mcp`
   re-reads the file.

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

   TODO(reviewer): exercise with a real MCP server and capture tool listing.

### CLI shortcut

There is no `agentseek mcp add` command today. Authoring is by file edit.

## Field reference

| Field | Required | Description |
| --- | --- | --- |
| `command` | yes | Binary on `PATH`, or a launcher like `uvx` / `npx`. |
| `args` | no | Argument list passed to `command`. |
| `env` | no | Extra env vars set when the server is spawned. |

The full field set is owned by `bub-mcp`. Where this page conflicts with the
plugin's source, the plugin wins.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tools from the server are missing | Spawn failed silently | Run `command args` manually outside agentseek to surface the error. |
| Server starts but auth fails | Token missing from `env` | Add the credential under the server's `env` object. |

## Rollback

Remove the server entry from `mcp.json`. Restart the process.

## Related

- How-to: `configure-mcp.md`, `configure-docker-workspace.md`
- Reference: `../reference/environment.md`
