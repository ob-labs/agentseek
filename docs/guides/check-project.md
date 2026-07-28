---
title: Check a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/lifecycle/diagnostics.py
  - src/agentseek/cli/lifecycle/json_output.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# Check a Project

Run readiness checks from the generated project directory with the installed CLI.
Prepare `.env` and run `agentseek task frontend` first when you expect a
passing check.

```bash
agentseek doctor
```

```text title="output excerpt"
ok   lifecycle.toml: Lifecycle spec is present.
ok   uv: uv is available.
ok   node: node is available.
ok   npm: npm is available.
ok   frontend/package.json: frontend/package.json is present.
ok   frontend/node_modules: frontend/node_modules is present.
ok   .env: .env is present.
ok   BUB_MODEL: BUB_MODEL is configured.
ok   BUB_API_KEY: BUB_API_KEY or BUB_OPENAI_API_KEY is configured.
ok   gateway cwd: . is present.
ok   frontend cwd: frontend is present.
```

Those checks come from required tools, paths, and environment entries.

```toml title=".agentseek/lifecycle.toml excerpt"
[tools]
required = ["uv", "node", "npm"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]
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

```text title="output excerpt"
ok   gateway: http://127.0.0.1:8088/agent/health is reachable.
ok   copilotkit: http://127.0.0.1:4000/health is reachable.
ok   frontend: http://127.0.0.1:5173 is reachable.
```

Live checks use the service health targets declared by the project.

```toml title=".agentseek/lifecycle.toml excerpt"
[checks.gateway]
type = "http"
target = "http://127.0.0.1:8088/agent/health"
timeout = 2
attempts = 3
```

## Use Diagnostics From Automation

Use JSON mode for a stable list of typed results. Add `--live` when the
services are already running.

```bash
agentseek doctor --json
agentseek doctor --live --json
```

A completed diagnostic run has `ok: true`. Read `data.passed` and the process
exit status to decide whether checks passed; declared live checks have
`state: "not_run"` unless `--live` is present. JSON mode writes one document to
stdout and no diagnostic prose to stderr.

Do not combine `--strict` with `--json`. That option conflict returns exit code
`2` in a structured error envelope.

## Next

- [Start the app](run-local-development.md)
- [Run project tasks](run-project-tasks.md)
- [See all command options](../reference/cli.md)
