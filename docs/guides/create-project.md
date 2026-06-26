---
title: Create a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - pyproject.toml
  - src/agentseek/cli/commands/create.py
  - templates/index.json
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
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

The prompt-free form is quiet when it succeeds. The generated project contains
the lifecycle spec that later commands read.

```text title="generated files excerpt"
my_bub_agent/
  .agentseek/lifecycle.toml
  .env.example
  frontend/package.json
```

```toml title=".agentseek/lifecycle.toml excerpt"
version = 1
template = "bub/default"
name = "My Bub Agent"
env_file = ".env"
```

Change into the generated directory.

```bash
cd my_bub_agent
```

## List Templates

```bash
agentseek create --list-templates
```

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
