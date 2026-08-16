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
- Declare tools under `[tools]` with a `required` list.
- Declare file and directory prerequisites under `[paths]` with a `required` list.
- Declare only environment variables AgentSeek should check under `[env.<name>]`. Defaults are lower priority than `env_file` and shell variables.
- Only non-dry-run `agentseek dev` resolves `env_file` once, overlays non-empty captured launch environment values, and reuses one immutable snapshot for checks and all long-running child processes.
- Lifecycle defaults are readiness-only. A dotenv `KEY=` remains present and empty; bare `KEY` contributes no child assignment.
- Bounded python-dotenv resolves physical bindings in order and falls back to the captured launch environment; the lifecycle schema adds no interpolation mode.
- For non-dry-run `agentseek dev`, a missing, undecodable, or malformed dotenv returns `exit 2` before any child starts; no partial snapshot or value-bearing diagnostic is allowed. Standalone `agentseek info` reports dotenv status, while standalone `agentseek doctor --strict` renders readiness failures and returns `exit 1`.
- `agentseek task` does not inherit lifecycle `env_file`.
- AgentSeek guarantees only the initial child environment/snapshot: it has resolved values, not source instructions. Compatible child configuration completion may fill absent keys but must not replace inherited present keys; arbitrary child code can mutate its own process environment.
- Keep process commands as direct argv arrays; do not add shell wrappers to repair precedence.
- Do not add duplicated override-loading: it is an authoring prohibition, not an AgentSeek enforcement claim. An agentseek-api child using this contract requires `agentseek-api >= 0.2.2`.
- Put public service URLs under `[services.<name>]`.
- Put long-running process commands under `[processes.<name>]`. Do not declare process-level environment overrides.
- Put task commands under `[tasks.<name>]`. Task `cwd` values are project-relative and must exist before the task starts.

Version 1 deliberately does not support optional tool/path checks, TCP checks,
process env overrides, or multiple env files. It adds no lifecycle-schema
interpolation mode; configured `env_file` parsing uses bounded python-dotenv,
which resolves physical bindings in order and falls back to the captured launch
environment.

## Command Semantics

- `agentseek create [spec]` creates a project from an AgentSeek-compatible template.
- `agentseek doctor [--live] [--strict]` checks the current project through the lifecycle spec.
- `agentseek dev [--dry-run] [--skip-check]` starts local development or prints the startup plan. `--skip-check` skips only the preliminary strict `doctor` pass; required lifecycle inputs are still enforced before processes start.
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
