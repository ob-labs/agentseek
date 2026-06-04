# Bub — contextseek template

Scaffolds a Bub-flavored agent project with a ContextSeek semantic memory
layer. Extends `bub/default` with a ctx HTTP API server and a seed script
that pre-loads example knowledge on first boot.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name (auto-derived). |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Port for `agentseek gateway` (default `8088`). |
| `frontend_port` | Vite dev server port (default `5173`). |
| `copilotkit_port` | CopilotKit Express runtime port (default `4000`). |
| `ctx_server_port` | FastAPI ctx HTTP server port (default `8089`). |
| `contextseek_storage_backend` | Storage backend (`memory` or `oceanbase`). |
| `contextseek_storage_path` | Local store path when using `memory` backend. |
| `contextseek_tenant` | ContextSeek tenant identifier. |

## Generated layout

```
<project_slug>/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── pyproject.toml
├── frontend/          # CopilotKit + Vite (unchanged from bub/default)
└── src/<project_slug>/
    ├── __init__.py
    ├── dev.py         # starts gateway + ctx server + frontend
    ├── seed.py        # idempotent example knowledge loader
    └── server.py      # FastAPI: /ctx/add  /ctx/overview  /ctx/retrieve
```
