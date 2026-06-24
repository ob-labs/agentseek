---
title: Run Local Development
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-23
sources:
  - src/agentseek/cli/commands/dev.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Run Local Development

Start the development stack from the generated project directory with the installed CLI.

```bash
agentseek dev
```

Preview the startup plan without launching services.

```bash
agentseek dev --dry-run
```

Skip the preliminary strict `doctor` pass when you already know the project
state. Core required inputs declared by the lifecycle spec are still enforced
before processes start.

```bash
agentseek dev --skip-check
```

Use `Ctrl+C` to stop the local development stack.

## Next

- [Check running services](check-project.md)
- [Run project tasks](run-project-tasks.md)
