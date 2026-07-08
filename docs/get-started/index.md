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
uv sync
npm install --prefix frontend
```

Set the model and provider credentials required by the selected template in
`.env` or the environment used to run AgentSeek.

`.env` is used by AgentSeek only for lifecycle environment checks declared by
the template. It is not automatically passed to child processes.

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
