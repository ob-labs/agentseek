---
title: Run Local Development
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/dev.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Run Local Development

Start the development stack from the generated project directory with the installed CLI.
Run `agentseek doctor` first when you expect startup to proceed without setup errors.

```bash
agentseek dev
```

Preview the startup plan without launching services.

```bash
agentseek dev --dry-run
```

```text title="output excerpt"
Startup plan
  Gateway: uv run bub gateway --enable-channel ag-ui
  Frontend: npm run dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit
```

The startup plan comes from process and service declarations.

```toml title=".agentseek/lifecycle.toml excerpt"
[processes.gateway]
command = ["uv", "run", "bub", "gateway", "--enable-channel", "ag-ui"]

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[services.app]
url = "http://127.0.0.1:5173"
```

Skip the preliminary strict `doctor` pass when you already know the project
state. Core required inputs declared by the lifecycle spec are still enforced
before processes start.

```bash
agentseek dev --skip-check
```

Use `Ctrl+C` to stop the local development stack.

## Next

- [Check running services](check-project.md)
- [Run project tasks](run-project-tasks.md)
