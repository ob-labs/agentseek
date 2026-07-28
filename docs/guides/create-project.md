---
title: Create a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - pyproject.toml
  - src/agentseek/data/catalog-lock.json
  - src/agentseek/cli/commands/create.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# Create a Project

Create a project with an explicit template path.

Install the CLI before running daily lifecycle commands.

```bash
uv tool install agentseek
```

```bash
agentseek create bub/default --no-input
```

The prompt-free form prints the generated directory and the next lifecycle
commands to run.

```text
Created my_bub_agent

Next:
  cd my_bub_agent
  agentseek info
  agentseek task --list
  agentseek doctor
```

The generated project contains the lifecycle spec that later commands read.

```text title="generated files excerpt"
my_bub_agent/
  .agentseek/lifecycle.toml
  .env.example
  frontend/package.json
```

```toml title=".agentseek/lifecycle.toml excerpt"
version = 2
template = "bub/default"
name = "My Bub Agent"
description = "Bub agent with a browser UI, CopilotKit runtime, and AG-UI gateway."
env_file = ".env"
guide = "README.md"
```

Change into the generated directory when you are ready to inspect or run it.

```bash
cd my_bub_agent
```

## List Templates

```bash
agentseek create --list-templates
```

This listing uses the registry snapshot embedded in AgentSeek 0.1.0 and works
offline. The selected lifecycle-v2 template is downloaded only when you
describe or create it, at the immutable catalog commit recorded by the CLI.

The shared CLI currently recognizes `bub`, `deepagents`, and `langchain`
template types. List only one type by passing it before `--list-templates`.

```bash
agentseek create bub --list-templates
```

## Select A Template By Type

Run each create form from a directory where the generated project directory
does not already exist.

```bash
agentseek create bub --template default --no-input
```

## Compatibility Entry Point

```bash
agentseek create --template
```

`--template` with no value lists templates. Prefer `--list-templates` in new scripts.

## Next

- [Inspect the project](inspect-project.md)
- [Check the project](check-project.md)
- [Run local development](run-local-development.md)
