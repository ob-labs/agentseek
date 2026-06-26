---
title: Run Project Tasks
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Run Project Tasks

List the tasks exposed by the generated project with the installed CLI.

```bash
agentseek task --list
```

```text title="output excerpt"
  frontend              Install frontend dependencies.
```

The task list comes from `[tasks.*]` entries in the lifecycle spec.

```toml title=".agentseek/lifecycle.toml excerpt"
[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

Run a project task by name.

```bash
agentseek task frontend
```

```text title="output excerpt"
added 945 packages, and audited 946 packages in 1m
```

This command runs the declared command from the project root. After it finishes,
`agentseek doctor` reports `frontend/node_modules` as present.

Tasks are declared by the generated project's lifecycle spec. If a task
declares `cwd`, AgentSeek runs the command from that project-relative directory
and reports a lifecycle error when it is missing.

## Next

- [Understand the lifecycle spec](../reference/lifecycle-spec.md)
- [See all command options](../reference/cli.md)
