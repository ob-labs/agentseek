# Bub — contextseek template

Scaffolds a Bub-based agent project with a ContextSeek semantic memory layer
and an AgentSeek lifecycle v1 spec. Extends `bub/default` with a ctx HTTP API
server and a seed task for loading example knowledge.

## Architecture

```text
uvx agentseek dev
  -> .agentseek/lifecycle.toml
    -> uv run bub gateway --enable-channel ag-ui
        -> BubFramework + ag-ui channel :{{ gateway_port }} /agent
    -> uv run ctx-server
        -> ContextSeek HTTP API :{{ ctx_server_port }} /ctx
    -> npm run dev
        -> Vite app :{{ frontend_port }} (/api/copilotkit/* proxied)
        -> Copilot Runtime :{{ copilotkit_port }} /api/copilotkit
```

Use `agentseek info`, `agentseek doctor`, `agentseek dev`, and `agentseek task`
from the generated project. Additional project tasks, including dependency
setup and seed loading, are declared in `.agentseek/lifecycle.toml`.
AgentSeek is the external lifecycle CLI; Bub remains the runtime framework.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name (auto-derived). |
| `author` | Project author. |
| `default_model` | Default `BUB_MODEL`. |
| `gateway_port` | Port for the Bub AG-UI gateway (default `8088`). |
| `frontend_port` | Vite dev server port (default `5173`). |
| `copilotkit_port` | CopilotKit Express runtime port (default `4000`). |
| `ctx_server_port` | FastAPI ctx HTTP server port (default `8089`). |
| `contextseek_storage_backend` | Storage backend. Defaults to `seekdb`; generated `.env.example` also includes optional OceanBase settings. |
| `contextseek_storage_path` | Reserved local ContextSeek store path input. |
| `contextseek_tenant` | ContextSeek tenant identifier. |

## Generated layout

```
<project_slug>/
├── .env.example
├── .gitignore
├── .agentseek/lifecycle.toml
├── Dockerfile
├── README.md
├── pyproject.toml
├── frontend/          # CopilotKit + Vite (unchanged from bub/default)
└── src/<project_slug>/
    ├── __init__.py
    ├── seed.py        # idempotent example knowledge loader
    └── server.py      # FastAPI: /ctx/add  /ctx/overview  /ctx/retrieve
```

## Runtime environment ownership

The generated `.env` is the readiness and env source for `agentseek info` and
`agentseek doctor`. Lifecycle v1 does not inject `.env` into child processes.
Runtime environment is owned by the launched processes and the caller's shell:
the Bub AG-UI channel and ctx server read `.env` themselves, Vite reads
`frontend/.env`, and shell variables override file values where the underlying
tools support that behavior.
