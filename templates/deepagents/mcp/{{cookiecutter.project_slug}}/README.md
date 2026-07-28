# {{ cookiecutter.project_name }}

DeepAgents application scaffolded with `agentseek create deepagents/mcp`.
It discovers MCP tools from validated stdio or HTTP connections and includes a
local calculator example plus a streamed React UI.

## Prerequisites

- Python 3.11 or newer with `uv`.
- Node.js `^20.19.0 || ^22.13.0 || >=24.0.0` with `npm`.

## Quickstart

Run `agentseek task sync`, `agentseek task frontend`, and
`agentseek task mcp-smoke`, then inspect with `agentseek doctor` and start both
development services with `agentseek dev`.

Copy `.env.example` to `.env` and set a provider credential before using the
agent. The MCP smoke task does not require a model key.

Both development servers bind to loopback by default. Shell exports and inline
assignments are inherited by both processes. To make both servers reachable
from another machine or container for one run, opt in explicitly:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```

For a persistent Vite-only bind setting, copy `frontend/.env.example` to
`frontend/.env` and edit `FRONTEND_HOST` there. `LANGGRAPH_HOST` must be a shell
export or inline assignment when `agentseek dev` starts. The root `.env` remains
the application/model configuration file; it does not configure either server
bind address.
