---
title: 03 — Add a skill and an MCP server
type: tutorial
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - .agents/skills/local-greeting/SKILL.md
  - .agents/mcp.json
---

# Add a skill and an MCP server

> **You will:** drop a project-local skill into `.agents/skills/<name>/SKILL.md`, declare an
> MCP server in `.agents/mcp.json`, and confirm that the agent picks both up.
> **You need:** the project from [02 — Build your first harness app](02-first-harness-app.md) (or any agentseek workspace) and
> `uv`. `bub-mcp` is already included with `agentseek`, so no extra install is required.

This tutorial covers the operational shape that every harness app eventually grows into:
*there is something in this workspace that the agent should be aware of without me hand-wiring it
into Python code.* Skills handle that for instructions/playbooks; MCP servers handle it for
tools and live data sources.

## 1. Write a project-local skill

Project-local skills live under `.agents/skills/<skill-name>/SKILL.md`. Bub discovers them
from the workspace automatically — no plugin install, no CLI command needed. The minimum
shape is one front-matter block plus a body, copied from
`.agents/skills/local-greeting/SKILL.md` in this checkout:

```markdown
---
name: local-greeting
description: Return a short greeting for quick smoke tests of a custom Bub skill.
---

Return exactly one sentence.
If the workspace path is available, mention it briefly.
```

Create the directory and file from the project root:

```bash
mkdir -p .agents/skills/local-greeting
$EDITOR .agents/skills/local-greeting/SKILL.md
```

Paste the snippet above into the file and save. The `name` field is what the agent uses to
invoke the skill; the `description` is what the model sees when choosing whether to use it.

Confirm the skill is visible:

```bash
uv run agentseek skills list
```

```text title="expected output"
Project Skills

documentation-writer ~/oceanbase/agentseek/.agents/skills/documentation-writer
  Agents: Codex, Cursor
local-greeting ~/oceanbase/agentseek/.agents/skills/local-greeting
  Agents: Codex, Cursor
github-repo-cards ~/oceanbase/agentseek/skills/github-repo-cards
  Agents: OpenClaw
langchain-cn-models ~/oceanbase/agentseek/skills/langchain-cn-models
  Agents: OpenClaw
```

Your `local-greeting` row should appear under **Project Skills**. The `Agents:` column lists
which clients have been wired to surface the skill — your generated app needs no extra
wiring because Bub reads the workspace skills directly.

> **Bundled vs project-local.** Bundled skills ship with the agentseek distribution under
> `skills/` and `src/skills/` (the bottom two rows above come from `skills/`).
> `.agents/skills/` is where you write your own skills. Do not edit the bundled
> directories. See [How to add skills](../how-to/add-skills.md) for the full taxonomy.

## 2. Declare an MCP server

`bub-mcp` reads `${BUB_HOME}/mcp.json` by default. With agentseek's defaults that resolves
to `.agentseek/mcp.json`. If you prefer the project-root convention (`.agents/mcp.json`),
set `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json` before starting the runtime.

Both files use the same shape. The one in this checkout (`.agents/mcp.json`) is the
canonical minimal example:

```json
{
  "mcpServers": {
    "time": {
      "type": "streamable_http",
      "url": "https://mcp.api-inference.modelscope.net/<your-id>/mcp"
    }
  }
}
```

Replace `<your-id>` with the path your MCP host gave you. For an stdio-based server (for
example a local script), use:

```json
{
  "mcpServers": {
    "my-tools": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "my_package.mcp_server"]
    }
  }
}
```

Drop the file at the right path for your setup:

```bash
# project-root style (recommended for harness apps)
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json

# or accept the agentseek default
mkdir -p .agentseek && $EDITOR .agentseek/mcp.json
```

The full list of MCP-related variables is in [Environment variables reference](../reference/environment.md); the trade-offs
between the two locations live in [How to configure MCP servers](../how-to/configure-mcp.md).

## 3. Watch the agent pick them up

Restart the gateway from your project so the new skill and MCP entries are loaded:

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

On startup the gateway logs each skill it discovered and each MCP server it connected to.
Send a prompt through your frontend (or via `uv run agentseek chat` from the project root)
that should trigger either capability:

- *"Greet me as the local-greeting skill"* — the model should call `local-greeting` and
  return a one-sentence reply that mentions the workspace path.
- *"What time is it right now?"* — if the `time` MCP server is reachable, the model should
  call its tool and return the answer.

If a skill is not picked up, run `uv run agentseek skills list` again and confirm your row
appears. If an MCP server is not picked up, confirm the file path matches
`AGENTSEEK_MCP_CONFIG_PATH` exactly.

## What you have now

- A project-local skill at `.agents/skills/local-greeting/SKILL.md` listed by
  `agentseek skills list` under **Project Skills**.
- An MCP config file at `.agents/mcp.json` (or `.agentseek/mcp.json`) declaring at least one
  server, with `AGENTSEEK_MCP_CONFIG_PATH` set if you chose the project-root path.
- A clear separation in your head between **skills** (instructions the model can read) and
  **MCP servers** (live tools the model can call).

## Where to go next

- For Bub-compatible Python plugins (rather than skills or MCP), see
  [How to install a plugin](../how-to/install-a-plugin.md).
- For the decision matrix — when to reach for a skill, an MCP server, or a contrib plugin —
  see [The extension model](../explanation/extension-model.md).
- For everything `agentseek skills` forwards to `npx-skills`, see
  `../reference/cli.md#skills`.
- For the full list of `AGENTSEEK_*` variables and their `BUB_*` aliases, see
  [Environment variables reference](../reference/environment.md).
