# LangChain — cli-remote template

Scaffolds a project that runs a graph via `langgraph dev` and bridges it
into agentseek through `LangGraphClientRunnable`. Mirrors the
`examples/langchain_cli_remote_agent` example.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `langgraph_url` | Default LangGraph Agent Server URL. |
| `assistant_id` | Graph / assistant id (matches `langgraph.json`). |
