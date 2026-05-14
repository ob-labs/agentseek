# AG-UI + LangChain (CopilotKit-style + AgentSeek)

This example follows the same ideas as the [LangChain CopilotKit integration guide](https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit), but runs through the agentseek gateway instead of mounting a separate FastAPI runtime next to LangGraph.

## At A Glance

| Field | Value |
| --- | --- |
| Python side | LangChain `create_agent(...)` with `CopilotKitState`, `CopilotKitMiddleware`, and structured-output middleware |
| Frontend | CopilotKit + Hashbrown UI |
| Gateway path | `agentseek gateway --enable-channel ag-ui` |
| Ports | frontend `5174`, runtime `4001`, gateway `8088` |
| Example-local verification | `uv run pytest examples/ag_ui_langchain/test_middleware.py` |

## Shape

- **Python**: `CopilotKitState`, `AgentContext` (including `output_schema`), `create_agent` with `normalize_context`, `CopilotKitMiddleware`, `apply_structured_output_schema`, and the guide’s system prompt.
  **Difference from the guide**: there is no FastAPI `add_langgraph_fastapi_endpoint` in-repo; the same agent runs on the **AgentSeek gateway** via **`agentseek-langchain`** `RunnableSpec` (`messages_spec`).
- **Frontend** — dedicated app under [`frontend/`](frontend/) (does **not** change [`examples/ag-ui/frontend`](../ag-ui/frontend)): CopilotKit plus **`@hashbrownai/core` / `@hashbrownai/react` (0.5 beta, `useUiKit` / `useJsonParser`)**, `useAgentContext` (`output_schema`), and an assistant markdown slot that parses structured JSON with `kit.render` (falls back to default markdown when content is not valid UI JSON), matching the [LangChain CopilotKit guide](https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit) flow.

**Config loading** uses **`pydantic-settings.BaseSettings`** in [`settings.py`](settings.py): repository root `.env` plus `examples/ag_ui_langchain/.env`, with `Field(..., validation_alias=AliasChoices(...))` over **`AGENTSEEK_*` / `BUB_*` / `OPENAI_*`** names.

The compatibility point is that [`build_agent()`](demo_binding.py) stays doc-shaped: ordinary LangChain `create_agent(...)` code with `CopilotKitState`, `CopilotKitMiddleware`, and the same middleware pattern shown in the guide. AgentSeek only adapts transport and forwards CopilotKit / AG-UI context into LangChain runtime `context`.

## Prerequisites

From the repository root:

```bash
uv sync --extra ag-ui --extra langchain
uv pip install -r examples/ag_ui_langchain/requirements.txt
```

`requirements.txt` mainly adds **`copilotkit`** (and explicitly **`pydantic-settings`** for the example settings module).

Model and gateway variables match the rest of agentseek: **`AGENTSEEK_MODEL`**, **`AGENTSEEK_API_KEY`**, **`AGENTSEEK_API_BASE`**. You can copy the model block from the root `.env` into **`examples/ag_ui_langchain/.env`** (see [`.env.example`](.env.example)). For **`openai:`** models, when `OPENAI_*` are unset, [`settings.py`](settings.py) bridges AgentSeek credentials into **`OPENAI_API_KEY`** / **`OPENAI_API_BASE`** via `apply_openai_env_bridge()` (called from [`demo_binding.py`](demo_binding.py) before `create_agent`).

## Configure

Recommended local env file:

```bash
cp examples/ag_ui_langchain/.env.example examples/ag_ui_langchain/.env
```

Then set:

- `AGENTSEEK_MODEL`, `AGENTSEEK_API_KEY`, `AGENTSEEK_API_BASE`
- `AGENTSEEK_LANGCHAIN_SPEC=ag_ui_langchain.demo_binding:build_spec`
- `AGENTSEEK_STREAM_OUTPUT=true`
- `PYTHONPATH=examples`

The commands below assume you start from the repository root and load both `.env` files with `uv run --env-file ...`.

## Run

**1. Gateway** (repository root):

```bash
uv run --env-file .env --env-file examples/ag_ui_langchain/.env agentseek gateway --enable-channel ag-ui
```

**2. Frontend** (second terminal) — this example’s Vite + Copilot Runtime (defaults **5174** / **4001** so the plain [`ag-ui`](../ag-ui/README.md) demo can keep **5173** / **4000**):

```bash
cd examples/ag_ui_langchain/frontend
npm install   # once
npm run dev
```

Open **`http://127.0.0.1:5174`**: CopilotKit → local Copilot Runtime → `HttpAgent` → gateway `/agent` → LangChain spec → AG-UI SSE.

See [`frontend/README.md`](frontend/README.md) and [`frontend/.env.example`](frontend/.env.example). Generic CopilotKit / Vite notes: [`../ag-ui/README.md`](../ag-ui/README.md).

## Verify

Smoke checks:

```bash
curl -s http://127.0.0.1:4001/health
cd examples/ag_ui_langchain/frontend
npm run build
```

Example-local Python verification:

```bash
uv run pytest examples/ag_ui_langchain/test_middleware.py
```

That test intentionally lives under `examples/` and is not collected by the repository-level `make test`. It covers only the example glue layer.

## Files

| File | Role |
| --- | --- |
| [`demo_binding.py`](demo_binding.py) | `build_spec()` → `messages_spec` + guide-aligned `create_agent` / CopilotKit middleware |
| [`middleware.py`](middleware.py) | `normalize_context`, `apply_structured_output_schema` (as in the guide) |
| [`settings.py`](settings.py) | `BaseSettings` + `AliasChoices` + OpenAI env bridge |
| [`requirements.txt`](requirements.txt) | Extra Python deps (`uv pip install -r …`) |
| [`.env.example`](.env.example) | Checklist; local `examples/ag_ui_langchain/.env` is not committed |
| [`test_middleware.py`](test_middleware.py) | Example-local regression test for schema normalization |
| [`frontend/`](frontend/) | Standalone CopilotKit + Hashbrown UI (Vite **5174**, runtime **4001**) |

## Limitations

- This is a demo integration, not a production deployment recipe.
- Structured UI depends on the model provider being able to satisfy LangChain structured output for the supplied schema.
- If the assistant reply is not valid UI JSON for the registered component schema, the frontend falls back to normal markdown rendering instead of coercing it.
