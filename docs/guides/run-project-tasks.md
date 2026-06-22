---
title: Run Project Tasks
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle.py
---

# Run Project Tasks

List the tasks exposed by the generated project.

```bash
uvx agentseek task --list
```

Run a project task by name.

```bash
uvx agentseek task info
```

Pass task arguments as `name=value` pairs.

```bash
uvx agentseek task doctor live=false strict=false
```

## Next

- [Understand the lifecycle file](../reference/lifecycle-file.md)
- [See all command options](../reference/cli.md)
