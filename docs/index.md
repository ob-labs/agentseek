---
title: AgentSeek Lifecycle Toolkit
type: explanation
audience: [A1, A2, A5]
runs: yes
verified_on: 2026-06-23
sources:
  - pyproject.toml
  - README.md
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/lifecycle/core.py
  - templates/index.json
---

# AgentSeek Lifecycle Toolkit

> **In short:** AgentSeek helps you move from an app template to a running local
> AI application through a small lifecycle command set.

## Read This First

AgentSeek gives generated apps a consistent local development workflow.

It creates the app, checks whether it is ready, and starts the services needed
for local development.

```text
AgentSeek CLI
  -> app template
    -> editable generated app
      -> lifecycle tasks
      -> local development stack
```

## Try One Template Path

Install the CLI for daily use.

```bash
uv tool install agentseek
```

The command below uses one Bub template. DeepAgents and LangChain templates use
the same lifecycle command shape.
Fill `.env` before running `agentseek doctor`; otherwise the readiness check
reports the missing credentials.

```bash
agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
$EDITOR .env
uv sync
npm install --prefix frontend
agentseek doctor
agentseek dev
```

## Lifecycle Commands

| Command | Use it when you want to |
| --- | --- |
| `agentseek create` | Create a project from a template. |
| `agentseek doctor` | Check files, environment, dependencies, and ports. |
| `agentseek dev` | Start the generated project's local development stack. |
| `agentseek info` | Inspect project metadata and local entry points. |
| `agentseek task` | Run project-defined tasks directly. |

## Understand The Workflow

A generated project carries its own lifecycle tasks.

AgentSeek exposes the common tasks as first-class commands. It also lets you
run project-specific tasks through `agentseek task`.

This keeps the workflow predictable while leaving app behavior in the generated
project.

## Current Focus

- Create editable apps from templates.
- Check local readiness before development.
- Run the local development stack.
- Inspect project metadata and entry points.
- Extend the app workflow with project tasks.

## Next Reads

- [Get started](get-started/index.md)
- [Create a project](guides/create-project.md)
- [Review the CLI](reference/cli.md)
