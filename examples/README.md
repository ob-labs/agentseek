# agentseek Examples

This directory contains runnable examples for the repository-level `agentseek` distribution and
its contrib packages.

## Available Examples

| Example | Purpose |
| --- | --- |
| [`ag-ui`](ag-ui/README.md) | CopilotKit + AG-UI + gateway (`agentseek-ag-ui`) without LangChain. |
| [`ag_ui_langchain`](ag_ui_langchain/README.md) | Dedicated [`frontend/README`](ag_ui_langchain/frontend/README.md) (CopilotKit + Hashbrown); LangChain `create_agent` + CopilotKit middleware via **`agentseek-langchain`** on the gateway. |
| [`langchain_deepagents`](langchain_deepagents/README.md) | How to connect a local `create_deep_agent(...)` runnable to **`agentseek-langchain`**. |
| [`langchain_cli_remote_agent`](langchain_cli_remote_agent/README.md) | How to connect a `langgraph dev` remote agent to **`agentseek-langchain`** through `LangGraphClientRunnable`. |

Examples are intentionally kept outside package source trees so they can show how the pieces are
installed and run together from a user workspace.
