---
title: 02 — Build your first harness app
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/run.py
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
---

# Build your first harness app

You will create a generated project, install its dependencies, and start the
local app loop.

## 1. Choose the starter

This tutorial uses `bub/default`. It is the smallest full harness app in the
repository template catalogue.

You can see the available starters first:

```bash
uvx agentseek create --list-templates
```

## 2. Generate the project

Choose a working directory for the generated project:

```bash
mkdir -p ~/projects
cd ~/projects
uvx agentseek create bub/default --no-input
```

The default project is named `my_bub_agent`.

```bash
find my_bub_agent -maxdepth 1 -mindepth 1 -printf "%f\n" | sort
```

You should see:

```text
.env.example
Dockerfile
README.md
frontend
pyproject.toml
src
```

## 3. Install dependencies

```bash
cd my_bub_agent
uv sync
npm install --prefix frontend
```

The generated project is now your working surface.

## 4. Configure the model

```bash
cp .env.example .env
```

Open `.env` and set `AGENTSEEK_API_KEY`. Set `AGENTSEEK_API_BASE` too if your
provider needs a custom endpoint.

## 5. Run locally

For a backend-only check:

```bash
uv run agentseek gateway --enable-channel ag-ui
```

For the frontend and gateway together:

```bash
uv run agentseek run --no-browser
```

Open `http://127.0.0.1:5173` when the frontend is ready. Stop either command
with `Ctrl-C`.

## What you have now

- A standalone project with its own `.venv`, `.env`, and source tree.
- A local app loop through `agentseek run`.
- A project you can edit without touching the AgentSeek repository.

## Next

- Add local behavior and tools: [Add a skill and MCP](03-add-a-skill-and-mcp.md).
- Run under Compose: [Run with Docker Compose](../how-to/run-with-docker-compose.md).
- Look up exact flags: [CLI reference](../reference/cli.md).
