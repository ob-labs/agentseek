---
title: Check a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/commands/doctor.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/duties.py"
---

# Check a Project

Run readiness checks from the generated project directory.

```bash
uvx agentseek doctor
```

Use strict mode in automation when warnings should also fail the check.

```bash
uvx agentseek doctor --strict
```

Use live mode after starting the app. It checks whether local services are
listening.

```bash
uvx agentseek doctor --live
```

## Next

- [Start the app](run-local-development.md)
- [See all command options](../reference/cli.md)
