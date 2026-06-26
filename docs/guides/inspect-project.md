---
title: Inspect a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/info.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Inspect a Project

Run `info` from the generated project directory.

```bash
agentseek info
```

```text title="output excerpt"
Project
  Root: /path/to/my_bub_agent
  Name: My Bub Agent
  Template: bub/default
  Lifecycle: .agentseek/lifecycle.toml / version 1

Entrypoints
  Dev: agentseek dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit

Environment
  Env file: .env (present)
  BUB_MODEL: set (.env)
  BUB_API_KEY: set (.env)
```

The entry points come from the lifecycle spec.

```toml title=".agentseek/lifecycle.toml excerpt"
[services.app]
url = "http://127.0.0.1:5173"

[services.gateway]
url = "http://127.0.0.1:8088/agent"

[services.copilotkit]
url = "http://127.0.0.1:4000/api/copilotkit"
```

Use verbose mode when you need loader details.

```bash
agentseek info --verbose
```

```text title="output excerpt"
Capabilities
  commands: dev, info, doctor
  tasks: frontend

Discovery
  Python: /path/to/python
  uv: /path/to/uv
  node: /path/to/node
  npm: /path/to/npm
```

## Next

- [Check the project](check-project.md)
- [Run local development](run-local-development.md)
