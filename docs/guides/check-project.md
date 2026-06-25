---
title: Check a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-23
sources:
  - src/agentseek/cli/commands/doctor.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Check a Project

Run readiness checks from the generated project directory with the installed CLI.
Prepare the project `.env` and dependencies first when you expect a passing check.

```bash
agentseek doctor
```

Use strict mode in automation when warnings should also fail the check.

```bash
agentseek doctor --strict
```

Use live mode after starting the app. It checks whether local services are
listening.

```bash
agentseek doctor --live
```

## Next

- [Start the app](run-local-development.md)
- [See all command options](../reference/cli.md)
