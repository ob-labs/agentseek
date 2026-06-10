---
title: 02 — Build your first harness app
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/commands/new.py
  - src/agentseek/cli/commands/dev.py
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
---

# Build your first harness app

You will create a project with `agentseek create`, sync that generated project,
configure a model, and run it locally.

## 1. Pick a template

List bundled templates:

```bash
uv run agentseek create --list-templates
```

This tutorial uses `bub/default` because it is the lightest full harness app.

## 2. Generate the project

Choose a working directory outside the AgentSeek checkout:

```bash
mkdir -p ~/projects
cd ~/projects
uvx agentseek create bub/default --no-input
```

The default project is named `my_bub_agent`.

```bash
ls -a my_bub_agent
```

Expected shape:

```text
Dockerfile   .env.example   frontend   pyproject.toml   README.md   src
```

## 3. Install project dependencies

```bash
cd my_bub_agent
uv sync
```

The generated project depends on `agentseek` and provides the same CLI command
groups as the repository checkout.

## 4. Configure the model

```bash
cp .env.example .env
```

Fill in `AGENTSEEK_API_KEY` and, if needed, `AGENTSEEK_API_BASE`. See
[Environment variables](../reference/environment.md) for the full table.

## 5. Run locally

For a backend-only smoke test:

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

For the full frontend + gateway loop:

```bash title="not executed in this run"
npm install --prefix frontend
uv run agentseek run --no-browser
```

Open `http://127.0.0.1:5173` when the frontend is ready.

## What you have now

- A standalone project with its own `.venv`, `.env`, and source tree.
- A verified project command path through `agentseek create` and `agentseek run`.
- A project you can edit without touching the AgentSeek repository.

## Next

- Add project behavior: [Add a skill and MCP](03-add-a-skill-and-mcp.md).
- Run under Compose: [Run with Docker Compose](../how-to/run-with-docker-compose.md).
- Inspect all flags: [CLI reference](../reference/cli.md).
