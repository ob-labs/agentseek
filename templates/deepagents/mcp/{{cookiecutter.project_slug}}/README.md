# {{ cookiecutter.project_name }}

DeepAgents application scaffolded with `agentseek create deepagents/mcp`.
It discovers MCP tools from validated stdio or HTTP connections and includes a
local calculator example plus a streamed React UI.

## Quickstart

Run `agentseek task sync`, `agentseek task frontend`, and
`agentseek task mcp-smoke`, then inspect with `agentseek doctor` and start both
development services with `agentseek dev`.

Copy `.env.example` to `.env` and set a provider credential before using the
agent. The MCP smoke task does not require a model key.

Both development servers bind to loopback by default. To make them reachable
from another machine or container, opt in explicitly:

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```
