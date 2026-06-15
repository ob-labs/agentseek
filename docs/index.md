---
title: AgentSeek documentation
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-06-12
hide_sidebar: true
sources:
  - README.md
  - mkdocs.yml
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# AgentSeek documentation

AgentSeek turns agent runtime data into a database workload: turns, context,
tool calls, tasks, feedback, checkpoints, memory, and observability data stay
queryable instead of being scattered across logs and side systems.

## Minimal Commands

```bash
uvx agentseek create deepagents/default --no-input
cd my_deepagent
cp .env.example .env
uv sync
uv pip install -r requirements.txt
export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC=my_deepagent.demo_binding:build_spec
export AGENTSEEK_AG_UI_PORT=18088
uv run agentseek gateway --enable-channel ag-ui
```

Use [Quick demo via the CLI](tutorials/01-quick-demo-cli.md) when you want to
try the harness before creating a project.

## Project Lifecycle

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/02-first-harness-app/">Create</a></h3>
    <p>Start from a template when you need an editable harness app.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/run-locally/">Run</a></h3>
    <p>Run the generated project locally after model credentials are set.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/03-add-a-skill-and-mcp/">Extend</a></h3>
    <p>Add project-local skills, MCP tools, plugins, or ContextSeek when the app needs them.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/build-and-deploy/">Ship</a></h3>
    <p>Build the image and generate deployment manifests from the project root.</p>
  </div>
</div>

## After the first run

- Use `deepagents/default` when you want the recommended AgentSeek harness app.
- Use `bub/default` when you want the lightest harness app without LangChain.
- Use `langchain/default` when a LangChain app should enter the AgentSeek runtime.
- Use `deepagents/research` or `deepagents/content-builder` for DeepAgents-shaped products.
- Add [ContextSeek](how-to/use-contextseek.md) when memory should become a first-class runtime capability.
- Read [Runtime data model](explanation/runtime-data-model.md) before choosing a durable storage backend.
- Browse [Hub](hub.md) for bundled and contrib integrations.
