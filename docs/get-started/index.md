---
title: Get Started
type: tutorial
audience: [A1, A2]
runs: yes
verified_on: 2026-06-23
sources:
  - pyproject.toml
  - README.md
  - templates/index.json
  - templates/bub/default/cookiecutter.json
---

# Get Started

Create one app, install its local dependencies, and start its development
workflow.

## Install the CLI

```bash
uv tool install agentseek
```

## Create an app

```bash
agentseek create bub/default --no-input
cd my_bub_agent
```

`bub/default` is one available template path. Other templates can use the same
lifecycle commands.

## Prepare the project

```bash
cp .env.example .env
$EDITOR .env
agentseek task --list
agentseek task frontend
```

Set the model and provider credentials required by the selected template in
`.env` or the environment used to run AgentSeek.

For non-dry-run `agentseek dev`, AgentSeek reads the project `env_file` once, overlays
non-empty launch variables once, and reuses that immutable snapshot for
readiness and every long-running process. Lifecycle defaults are checks only.
One-shot `agentseek task` commands keep their normal launch environment and do
not inherit `env_file`.

## Check and run

Run the readiness check after `.env` and local dependencies are prepared.

```bash
agentseek doctor
agentseek dev
```

Use `Ctrl+C` to stop the local development stack.

## Next

- [Create a project with another template](../guides/create-project.md)
- [Check local readiness](../guides/check-project.md)
- [Review the command surface](../reference/cli.md)
