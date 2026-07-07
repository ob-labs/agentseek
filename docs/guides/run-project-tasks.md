---
title: Run Project Tasks
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-07-07
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
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

## Recommended Agent Skill Packs

Some templates expose optional tasks that install external skill packs for
coding agents. These remain project tasks, not root AgentSeek subcommands.

seekdb-heavy templates expose:

```bash
agentseek task seekdb-skills
```

That task runs:

```bash
npx skills add oceanbase/seekdb-ecology-plugins --all
```

Purpose: install recommended seekdb skills for supported coding agents so the
agent can help with seekdb setup, usage, and troubleshooting.

Prerequisites: Node.js with `npx`, network access to the npm registry and the
skill pack repository, and a coding agent supported by the external `skills`
CLI. Command syntax was checked against the `skills` npm package README on
2026-07-07.

Use `agentseek task --list` inside the generated project to discover whether a
template offers this task.

## Next

- [Understand the lifecycle spec](../reference/lifecycle-spec.md)
- [See all command options](../reference/cli.md)
