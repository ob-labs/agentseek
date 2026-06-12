---
title: 03 — Add a skill and an MCP server
type: tutorial
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - .agents/skills/local-greeting/SKILL.md
  - .agents/mcp.json
---

# Add a skill and an MCP server

You will add one project-local skill and one MCP server declaration to the
project from [the first harness app tutorial](02-first-harness-app.md).

Skills give the model project-specific instructions. MCP servers give the
runtime tool access.

## 1. Add a local skill

Run this from your generated project root:

```bash
mkdir -p .agents/skills/local-greeting
cat > .agents/skills/local-greeting/SKILL.md <<'EOF'
---
name: local-greeting
description: Return a short greeting for quick smoke tests of a custom Bub skill.
---

Return exactly one sentence.
If the workspace path is available, mention it briefly.
EOF
```

The runtime discovers project-local skills from `.agents/skills/` when it starts.

## 2. Add an MCP config

Create `.agents/mcp.json`:

```bash
mkdir -p .agents
cat > .agents/mcp.json <<'EOF'
{
  "mcpServers": {
    "time": {
      "type": "streamable_http",
      "url": "https://mcp.api-inference.modelscope.net/<your-id>/mcp"
    }
  }
}
EOF
```

Replace `<your-id>` with the path from your MCP host. Then point AgentSeek at
the file:

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
```

Your runtime also needs MCP support installed. If this project does not already
include it, use [Configure MCP servers](../how-to/configure-mcp.md).

## 3. Restart the runtime

```bash
uv run agentseek gateway --enable-channel ag-ui
```

Try prompts that should use the new capabilities:

- `Greet me as the local-greeting skill.`
- `What time is it right now?`

If the skill is not used, confirm
`.agents/skills/local-greeting/SKILL.md` exists and restart the runtime.
If the MCP tool is not available, confirm `AGENTSEEK_MCP_CONFIG_PATH` points to
the file you created.

## What you have now

- A project-local skill under `.agents/skills/`.
- An MCP server declaration in `.agents/mcp.json`.
- A project that can grow through instructions and tools without changing the
  application code first.

## Next

- Add more skills: [How to add skills](../how-to/add-skills.md).
- Configure more MCP servers: [Configure MCP servers](../how-to/configure-mcp.md).
- Choose between extension types: [The extension model](../explanation/extension-model.md).
