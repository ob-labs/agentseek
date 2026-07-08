---
title: Local Execution Modes
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-25
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/task.py
---

# Local Execution Modes

Use this page when you need to choose the right local entry point for a generated AgentSeek project. It summarizes the project lifecycle commands without repeating the full [CLI reference](../reference/cli.md).

## Choose an entry point

| Goal | Command | Where to run it |
| --- | --- | --- |
| Check project files, environment, dependencies, and optional live services | `agentseek doctor` | Generated project root |
| Preview the development startup plan | `agentseek dev --dry-run` | Generated project root |
| Start the local development stack | `agentseek dev` | Generated project root |
| Skip the preliminary strict doctor pass before startup | `agentseek dev --skip-check` | Generated project root |
| List template-defined tasks | `agentseek task --list` | Generated project root |
| Run one template-defined task | `agentseek task <name>` | Generated project root |

## Readiness checks: `agentseek doctor`

Use `agentseek doctor` before starting the stack when you want fast feedback on missing files, environment values, dependencies, and ports.

```bash
agentseek doctor
```

Use strict or live checks when you need stronger validation.

```bash
agentseek doctor --strict
agentseek doctor --live
```

See [Check a Project](check-project.md) for the full readiness workflow.

## Development stack: `agentseek dev`

Use `agentseek dev` when you want AgentSeek to start the long-running processes declared by the lifecycle spec.

```bash
agentseek dev
```

Preview the startup plan without launching processes.

```bash
agentseek dev --dry-run
```

Skip the preliminary strict `doctor` pass only when you already know the project state.

```bash
agentseek dev --skip-check
```

See [Run Local Development](run-local-development.md) for examples of the generated startup plan.

## Project tasks: `agentseek task`

Use `agentseek task` for one-shot commands declared by the template, such as dependency install, frontend setup, or checks.

```bash
agentseek task --list
agentseek task frontend
```

See [Run Project Tasks](run-project-tasks.md) for task examples and expected output.

## Related

- [Check a Project](check-project.md)
- [Run Local Development](run-local-development.md)
- [Run Project Tasks](run-project-tasks.md)
- [CLI reference](../reference/cli.md)
