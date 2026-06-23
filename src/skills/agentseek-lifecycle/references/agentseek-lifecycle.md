# AgentSeek Lifecycle Reference

## Public Contract

AgentSeek-managed projects expose lifecycle behavior through a `duties.py` file in the project root.

Expected lifecycle metadata:

```python
AGENTSEEK = {
    "version": 1,
    "template": "bub/default",
}
```

Expected lifecycle tasks:

- `doctor`: check local readiness.
- `dev`: run the local development stack.
- `info`: print project metadata and entry points.

Projects may expose additional tasks. Run them through `agentseek task`.

## Command Semantics

- `agentseek create [spec]` creates a project from an AgentSeek-compatible template.
- `agentseek doctor [--live] [--strict]` checks the current project.
- `agentseek dev [--dry-run] [--skip-check]` starts local development or prints the startup plan.
- `agentseek info [--verbose]` prints project summary and lifecycle details.
- `agentseek task --list` lists project-defined tasks.
- `agentseek task <name> key=value` runs project-defined tasks with Duty-style arguments.

## Compatibility Rules

- Keep `AGENTSEEK["version"]` compatible with the installed AgentSeek release.
- Keep `AGENTSEEK["template"]` equal to the template identity shown to users, such as `bub/default`.
- Keep generated README instructions aligned with actual lifecycle commands.
- Keep `doctor` fast and deterministic.
- Keep `dev --dry-run` side-effect free.
- Keep `info` copyable and useful before the project is running.
- Use AgentSeek through its CLI from generated projects.

## Public Validation

Use these checks for generated projects:

```bash
agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek task --list
```

Use these checks when debugging running services:

```bash
agentseek doctor --live
```

If a lifecycle command fails, inspect the generated project's `duties.py`, `.env`, dependency files, and README before assuming an AgentSeek CLI bug.
