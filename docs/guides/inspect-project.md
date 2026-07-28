---
title: Inspect a Project
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/lifecycle/json_output.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
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
  Lifecycle: .agentseek/lifecycle.toml / version 2

Entrypoints
  Dev: agentseek dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit

Environment
  Env file: .env (present)
  BUB_MODEL: set (.env)
  BUB_API_KEY: set (.env)

Lifecycle Tasks
  frontend: Install frontend dependencies.

Next
  agentseek task --list
  agentseek doctor
  agentseek dev
```

The entry points and project tasks come from the lifecycle spec.

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

## Read The Project From Desktop Or Another Tool

Use JSON mode when another program needs stable service topology and actions.

```bash
agentseek info --json
```

```json title="pretty-printed excerpt"
{
  "schema_version": 1,
  "command": "info",
  "ok": true,
  "lifecycle_version": 2,
  "data": {
    "metadata_complete": true,
    "services": [
      {
        "id": "app",
        "name": "Application",
        "kind": "web",
        "display": "default",
        "primary": true
      }
    ],
    "actions": [
      {
        "id": "service:app:open",
        "type": "open_url",
        "label": "Open Application",
        "service_id": "app",
        "url": "http://127.0.0.1:5173"
      }
    ]
  },
  "error": null
}
```

The actual wire output is one compact JSON line. Consumers should use the
provided `actions` instead of reconstructing behavior from display text.

## Next

- [Check the project](check-project.md)
- [Run local development](run-local-development.md)
