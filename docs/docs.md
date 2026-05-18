# Docs

This section is the core documentation for the built-in `agentseek` distribution layer.

Use it when you want the shortest path from "what is this project?" to "how do I run it and extend
it in a real workspace?"

## Read by goal

<div class="terminal-grid terminal-grid-3">
  <div class="terminal-card">
    <h3><a href="getting-started/">Getting started</a></h3>
    <p>Start here when you want a working local run or a Docker Compose setup with the least ceremony.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="configuration/">Configuration</a></h3>
    <p>Use the reference page for exact aliases, paths, defaults, and precedence rules.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="extensions/">Extensions</a></h3>
    <p>Use the guide when you need to add instructions, skills, MCP config, or Bub-compatible plugins.</p>
  </div>
</div>

## Documentation boundary

The `Docs` section focuses on what ships as the main distribution:

- the `agentseek` CLI entry point
- project-local runtime defaults such as `.agentseek`
- `AGENTSEEK_*` aliases for Bub-compatible settings
- bundled skills under `src/skills`

Larger integrations keep their complete setup and runtime details next to their code under
`contrib/`. Use [Hub](hub.md) when you want a repository-wide inventory instead of product docs.
