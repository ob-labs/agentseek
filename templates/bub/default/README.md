# Bub — default template

Scaffolds a minimal Bub-flavored agent project: an AG-UI gateway plus a
CopilotKit-based frontend that streams messages through it. Mirrors
`examples/ag-ui`. No LangChain layer is required.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default port for `agentseek gateway`. |
| `frontend_port` | Vite dev server port for the frontend. |
