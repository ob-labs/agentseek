---
title: Run Project Tasks
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-23
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle/core.py
---

# Run Project Tasks

List the tasks exposed by the generated project with the installed CLI.

```bash
agentseek task --list
```

Run a project task by name.

```bash
agentseek task frontend
```

Tasks are declared by the generated project's lifecycle spec. If a task
declares `cwd`, AgentSeek runs the command from that project-relative directory
and reports a lifecycle error when it is missing.

## Next

- [Understand the lifecycle spec](../reference/lifecycle-spec.md)
- [See all command options](../reference/cli.md)
