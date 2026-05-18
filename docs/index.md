---
hide_sidebar: true
---

<div class="landing-hero">
  <p class="landing-kicker">$ agentseek</p>
  <h1>Database-native agent runtime, packaged for real projects</h1>
  <p class="landing-lead">
    agentseek packages Bub with project-local defaults, `AGENTSEEK_*` aliases, bundled skills, and
    a workspace-first runtime layout.
  </p>
  <div class="landing-actions">
    <a class="terminal-button primary" href="getting-started/">Get started</a>
    <a class="terminal-button" href="docs/">Read docs</a>
    <a class="terminal-button" href="hub/">Explore hub</a>
  </div>
</div>

## Quick Start

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

Configure a model, then start a local session:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

## Explore

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">Docs</a></h3>
    <p>Read setup, configuration, and extension guidance for the main distribution.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="hub/">Hub</a></h3>
    <p>Browse the repository inventory of contrib packages and skills.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="blog/">Blog</a></h3>
    <p>Read introductions, migration notes, and workflow stories around the project.</p>
  </div>
</div>
