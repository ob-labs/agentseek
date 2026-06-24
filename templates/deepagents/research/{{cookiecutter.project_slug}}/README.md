# {{ cookiecutter.project_name }}

Pure DeepAgents research agent scaffolded with `agentseek create deepagents/research`.

The backend serves a `create_deep_agent(...)` graph through `langgraph dev`.
The frontend streams user messages, tool calls, optional sub-agent delegation,
DeepAgents todos, and the final markdown answer. AgentSeek is only used as an
external template and lifecycle tool; this project declares local behavior in
`.agentseek/lifecycle.toml`.

## Quickstart

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

uvx agentseek task backend
uvx agentseek task frontend

uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
```

Use `uvx agentseek task --list` to see the one-shot setup tasks exposed by the
lifecycle spec. After `uvx agentseek dev` starts both processes, run
`uvx agentseek doctor --live` from another terminal to check the declared local
service endpoints.

The LangGraph backend defaults to `http://127.0.0.1:{{ cookiecutter.langgraph_port }}`.
The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Environment

`agent.py` uses `AGENTSEEK_MODEL_PROVIDER` to choose a native LangChain provider
integration for OpenAI, Anthropic, or Gemini. Fill only the credential block for
the selected provider in `.env`. If that provider's base URL is blank, LangChain
uses the official endpoint.

If you change `AGENTSEEK_MODEL_PROVIDER`, also change `AGENTSEEK_MODEL` to a
model served by that provider. The generated app defaults to provider `openai`
and model `gpt-4.1-mini`, so leaving `OPENAI_API_BASE` blank targets the
official OpenAI endpoint. `AGENTSEEK_MODEL` can also be supplied through the
compatibility aliases `DEEPAGENTS_MODEL` or `BUB_MODEL`.

`TAVILY_API_KEY` is required for the `tavily_search` tool. The lifecycle spec
checks that one provider API key exists through `OPENAI_API_KEY` plus the
`ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` aliases; it does not validate that the
key matches the selected provider.

`frontend/.env` only controls the browser app's LangGraph URL and Vite port.

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
Research what LangGraph 1.0 added vs 0.x. Cite sources.
```

Expected behavior:

- A live **Research plan** todo panel appears when the agent writes todos.
- Tool cards appear for `tavily_search` and, when the model delegates,
  `task` as a "Sub-agent: research-agent" card.
- Each card expands while running, then collapses after its result lands.
- The final assistant response renders as markdown with linked citations.
