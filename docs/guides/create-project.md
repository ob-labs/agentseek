---
title: Create a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/commands/create.py
  - templates/index.json
---

# Create a Project

Create a project from a template path.

```bash
uvx agentseek create bub/default --no-input
```

Change into the generated directory.

```bash
cd my_bub_agent
```

## List templates

```bash
uvx agentseek create --template
```

## Choose a template by type

```bash
uvx agentseek create bub --template default --no-input
```

## Next

- [Check the project](check-project.md)
- [Run local development](run-local-development.md)
