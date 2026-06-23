---
title: Create a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-23
sources:
  - src/agentseek/cli/commands/create.py
  - templates/index.json
---

# Create a Project

Create a project with an explicit template path.

```bash
uvx agentseek create bub/default --no-input
```

Change into the generated directory.

```bash
cd my_bub_agent
```

## List Templates

```bash
uvx agentseek create --list-templates
```

List only `bub` templates.

```bash
uvx agentseek create bub --list-templates
```

## Select A Template By Type

```bash
uvx agentseek create bub --template default --no-input
```

Specify the template source branch when the template is not on the default branch.

```bash
uvx agentseek create bub/default --checkout dev --no-input
```

## Compatibility Entry Point

```bash
uvx agentseek create --template
```

`--template` with no value lists templates. Prefer `--list-templates` in new scripts.

## Next

- [Check the project](check-project.md)
- [Run local development](run-local-development.md)
