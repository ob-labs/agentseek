---
title: Run Local Development
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/commands/dev.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/duties.py"
---

# Run Local Development

Start the development stack from the generated project directory.

```bash
uvx agentseek dev
```

Preview the startup plan without launching services.

```bash
uvx agentseek dev --dry-run
```

Skip the readiness check when you already know the project state.

```bash
uvx agentseek dev --skip-check
```

Use `Ctrl+C` to stop the local development stack.

## Next

- [Check running services](check-project.md)
- [Run project tasks](run-project-tasks.md)
