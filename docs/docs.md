---
title: Documentation
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-30
sources:
  - README.md
  - mkdocs.yml
  - docs/tutorials/index.md
  - docs/how-to/index.md
  - docs/explanation/index.md
  - docs/reference/index.md
---

# Documentation

Start from the quadrant that matches the job you are doing right now.

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/">Tutorials</a></h3>
    <p>Guided end-to-end walkthroughs. Use these when you want a clean starting point and a concrete result at the end.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">How-to</a></h3>
    <p>Task-focused recipes. Use these when you already know the system and need the shortest path to one outcome.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="explanation/">Explanation</a></h3>
    <p>Design rationale and mental models. Use these when you want to understand why agentseek is shaped this way.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">Reference</a></h3>
    <p>Canonical facts: environment variables, CLI commands, file layout, packages, templates, and Docker.</p>
  </div>
</div>

## Suggested entry points

- New to the project: start with [Quick demo (CLI)](tutorials/01-quick-demo-cli.md).
- Building an app: read [Command overview](explanation/cli-surface.md), then [First harness app](tutorials/02-first-harness-app.md).
- Coming from LangChain / DeepAgents: read [LangChain relationship](explanation/langchain-relationship.md), then pick a template from [Templates reference](reference/templates.md).
- Operating a workspace: go to [How-to guides](how-to/index.md), especially Docker Compose and gateway pages.
- Looking up exact behaviour: open [Reference](reference/index.md).
