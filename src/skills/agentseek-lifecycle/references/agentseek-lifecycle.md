# AgentSeek Lifecycle Reference

## Public Contract

AgentSeek-managed projects expose lifecycle behavior through:

```text
.agentseek/lifecycle.toml
```

The spec is the single lifecycle contract.

Required lifecycle commands:

- `doctor`: check local readiness.
- `dev`: run the local development stack.
- `info`: print project metadata and entry points.

Projects may expose additional spec tasks. Run them through `agentseek task`.

## Spec Rules

- Keep `version = 1`.
- Declare tools under `[tools]` with `required` and `optional` lists.
- Declare file and directory prerequisites under `[paths]`.
- Declare environment variables under `[env.<name>]`.
- Put public service URLs under `[services.<name>]`.
- Put long-running process commands under `[processes.<name>]`.
- Put optional task commands under `[tasks.<name>]`.

## Command Semantics

- `agentseek create [spec]` creates a project from an AgentSeek-compatible template.
- `agentseek doctor [--live] [--strict]` checks the current project through the lifecycle spec.
- `agentseek dev [--dry-run] [--skip-check]` starts local development or prints the startup plan.
- `agentseek info [--verbose]` prints project summary and lifecycle details.
- `agentseek task --list` lists project-defined tasks.
- `agentseek task <name>` runs project-defined spec tasks.

## Compatibility Rules

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

If a lifecycle command fails, inspect the generated project's `.agentseek/lifecycle.toml`, `.env`, dependency files, and README before assuming an AgentSeek CLI bug.
