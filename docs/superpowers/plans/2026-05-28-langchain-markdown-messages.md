# langchain/markdown-messages Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure (no agentseek wrapper) `langchain/markdown-messages` cookiecutter template — a Python `create_agent` graph served over `langgraph dev`, paired with a Vite + React + TypeScript frontend that streams responses via `useStream` and renders them as markdown.

**Architecture:** Two processes. The backend exports a `graph` symbol from `agent.py` (`create_agent(model, tools=[], system_prompt=...)`), declared in `langgraph.json`, served by `langgraph dev` on `:2024`. The frontend (`:5174`) calls `useStream({assistantId: "agent", apiUrl: VITE_LANGGRAPH_API_URL})` to stream messages and feeds each message's `content` through `react-markdown` + `remark-gfm` so tables, lists, and code blocks render.

**Tech Stack:** Python 3.12, `langchain>=1.0`, `langchain-openai>=0.3`, `python-dotenv`, and `langgraph-cli[inmem]>=0.4` (which provides `langgraph dev`). All four are project dependencies — see "Why `langgraph dev` is a project dep" below. Vite + React 18 + TS, `@langchain/react@~0.3.5` (see "Why the `@langchain/react` pin" below), `react-markdown`, `remark-gfm`. Default LLM: SiliconFlow's OpenAI-compatible API at `https://api.siliconflow.cn/v1`, model `deepseek-ai/DeepSeek-V3` (chosen because it reliably produces well-formed markdown — `Qwen/Qwen2.5-7B-Instruct` and `Qwen3.5-9B` were tried and rejected: the former is too weak to produce structured output, the latter is a reasoning model that returns content via `reasoning_content` instead of `content`).

---

## Background — what you need to know

You are adding a new cookiecutter template under `templates/langchain/markdown-messages/`. You do not modify the agentseek runtime, the CLI, or any existing template. The render-check test from `2026-05-27-template-foundation.md` (already in main) will automatically pick up the new template via parametrize.

**Why "pure".** A pure template has **no** dependency on `agentseek-langchain`, `agentseek-ag-ui`, or `agentseek` itself, and the generated code does not call `messages_spec(...)`. The whole point is that a developer who knows LangChain can read the generated project without learning agentseek's wrappers first. See `templates/CONTRIBUTING.md` § "Pure vs agentseek-wrapped templates".

**The `.env` bridge.** The generated agent uses `init_chat_model(<id>, model_provider="openai")`, which reads `OPENAI_API_KEY` and `OPENAI_API_BASE` from the environment. To let users with only `AGENTSEEK_API_KEY` / `AGENTSEEK_API_BASE` in their `.env` "just work", we copy the 4-line bridge from `templates/CONTRIBUTING.md` near the top of `agent.py` (after `load_dotenv()`). This is documented convenience, not a hidden coupling — `.env.example` lists both pairs.

**Why `langgraph dev`.** `useStream` speaks the LangGraph protocol. The upstream-canonical way to expose a `create_agent` over that protocol is `langgraph dev`, which reads `langgraph.json`, imports the named graph, and serves it on `:2024` with the right endpoints. No custom FastAPI server needed.

**Why `langgraph dev` is a project dep, not a global tool.** `langgraph dev` runs the graph **inside the same Python environment it was installed into** — it adds the project dir to `sys.path` but does **not** install the `dependencies` array from `langgraph.json` anywhere (that array is only used by `langgraph build` for Docker). So if `langgraph-cli` lives in an isolated venv (`uv tool install`) and `langchain` lives in the project venv, the graph import fails with `ModuleNotFoundError: No module named 'langchain'`. The fix is to put `langgraph-cli[inmem]` in the project's `pyproject.toml` so `uv sync` installs it next to `langchain`, and run it with `uv run langgraph dev`. This matches the upstream `pip install "langgraph-cli[inmem]"` instruction.

**Why the `@langchain/react` pin (`~0.3.5`, not `^1.0`).** `@langchain/react@1.0+` depends on a newer `@langchain/langgraph-sdk` (1.9.x) whose `useStream` hits `POST /threads/{thread_id}/commands` on every submit. That endpoint exists in the hosted LangGraph Platform but **not** in `langgraph-api < 0.9.0`, which is what `langgraph-cli[inmem] 0.4.x` ships (the CLI caps `langgraph-api < 0.9.0`, and there's no `langgraph-cli` line that pulls a 0.9.x server yet — `langgraph-api 0.9.0` was published 2026-05-27, the day before this plan). The symptom is a `404 Not Found — {"detail":"Not Found"}` in the UI, the AI message never arrives. There is no client opt-out (the `multitaskStrategy` hook option exists but only controls server-side concurrent-run handling, not which endpoint the client hits). The workaround is `~0.3.5`, which keeps `@langchain/react` on the 0.3.x train. `0.3.5` itself pins `@langchain/langgraph-sdk` to **exact `1.8.10`** transitively, so a same-line patch bump (e.g. 0.3.6) won't change the SDK. Bump the pin when `langgraph-cli` releases a line whose `[inmem]` extra allows `langgraph-api >= 0.9.0`. This is a known short-lived constraint, not a permanent setting — call it out in the generated README.

**Cookiecutter variable conventions** (from existing templates):
- Use snake_case for cookiecutter variables.
- `project_slug` defaults to `{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}`.
- Ports are strings in `cookiecutter.json` (cookiecutter doesn't natively support ints).
- The `_agentseek_source_path` / `_agentseek_source_url` convention used by wrapped templates is for installing the agentseek runtime as an editable dep. **Pure templates do not need it** — omit those variables entirely.

**The live test credentials for verification steps** (do NOT commit, do NOT put in template defaults):

```bash
# Used by every "verify" step below. Export once at the start of any verification session.
export AGENTSEEK_API_KEY="sk-rugfpsgkcnslyqaumbuugsluxnvreemaczqnyiqejgpbgoeu"
export AGENTSEEK_API_BASE="https://api.siliconflow.cn/v1"
```

The template defaults `default_model` to `deepseek-ai/DeepSeek-V3` and passes `model_provider="openai"` as a kwarg to `init_chat_model`. SiliconFlow's OpenAI-compatible endpoint accepts any of its catalog model ids verbatim.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `templates/langchain/markdown-messages/cookiecutter.json` | Create | Vars: `project_name`, `project_slug`, `author`, `system_prompt`, `default_model`, `langgraph_port`, `frontend_port` |
| `templates/langchain/markdown-messages/README.md` | Create | Template-level: Inputs table + Generated layout tree |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/pyproject.toml` | Create | `requires-python = ">=3.12"`, deps: `langchain>=1.0`, `langchain-openai>=0.3`, `langgraph-cli[inmem]>=0.4`, `python-dotenv` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/langgraph.json` | Create | Points `agent` graph at `./src/{{slug}}/agent.py:graph`, loads `./.env` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example` | Create | OPENAI + AGENTSEEK env pairs, port defaults |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.gitignore` | Create | `.env`, `node_modules`, `dist`, `__pycache__`, `.venv`, `.langgraph_api/` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/README.md` | Create | Setup / Run (two-terminal) / Smoke test sections |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py` | Create | empty package marker |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/agent.py` | Create | `load_dotenv()` → bridge → `init_chat_model` → `graph = create_agent(...)` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/package.json` | Create | React 18, `@langchain/react`, `@langchain/core`, `react-markdown`, `remark-gfm`, Vite, TS |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/tsconfig.json` | Create | Vite + React TS config (ESNext modules, JSX react-jsx) |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/tsconfig.node.json` | Create | Vite config compilation |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/vite.config.ts` | Create | React plugin, port from `FRONTEND_PORT` env or `{{cookiecutter.frontend_port}}` default |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/index.html` | Create | `<div id="root">` + script tag for `main.tsx` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/.env.example` | Create | `VITE_LANGGRAPH_API_URL=http://127.0.0.1:{{ langgraph_port }}` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/.gitignore` | Create | `node_modules`, `dist`, `.env` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/main.tsx` | Create | Mount `<App />` on `#root` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/App.tsx` | Create | `useStream` hook, input box, message list with `<ReactMarkdown>` |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/styles.css` | Create | Minimal chat + markdown styles |
| `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/vite-env.d.ts` | Create | `/// <reference types="vite/client" />` |
| `templates/index.json` | Modify | Append `"langchain/markdown-messages": "..."` |

No source or existing-template changes.

---

## Task 1: Cookiecutter shell + Python agent

Stand up the template directory, the empty Python package, and the `create_agent` graph wired to `init_chat_model`. By the end of this task, the render-check from the foundation plan still passes, **and** rendering this template into `/tmp/agentseek-e2e/` produces a project where `langgraph dev` boots and a `curl` against `POST /runs/wait` returns a streamed AI message.

**Files:**
- Create: `templates/langchain/markdown-messages/cookiecutter.json`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/pyproject.toml`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/langgraph.json`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.gitignore`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/agent.py`

The template-level `README.md` and the generated-project `README.md` are deferred to Task 4 so this task stays focused.

- [ ] **Step 1: Create the template directory and `cookiecutter.json`**

```bash
mkdir -p 'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}'
```

Write `templates/langchain/markdown-messages/cookiecutter.json` with this exact content:

```json
{
  "project_name": "Markdown Messages Agent",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
  "author": "Your Name",
  "system_prompt": "You are a helpful assistant. Format your responses in markdown — use headings, lists, tables, and fenced code blocks where they help readability.",
  "default_model": "deepseek-ai/DeepSeek-V3",
  "langgraph_port": "2024",
  "frontend_port": "5174"
}
```

Note: **no** `_agentseek_source_path` / `_agentseek_source_url` — this is a pure template, the generated project does not depend on any agentseek package.

- [ ] **Step 2: Write `pyproject.toml`**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/pyproject.toml`:

```toml
[project]
name = "{{ cookiecutter.project_slug }}"
version = "0.1.0"
description = "{{ cookiecutter.project_name }} — a LangChain create_agent served with langgraph dev and streamed to a React frontend via useStream."
authors = [{ name = "{{ cookiecutter.author }}" }]
requires-python = ">=3.12"
dependencies = [
    "langchain>=1.0",
    "langchain-openai>=0.3",
    "langgraph-cli[inmem]>=0.4",
    "python-dotenv>=1.0",
]

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

No `[tool.uv.sources]` block — pure templates fetch deps from PyPI normally. `langgraph-cli[inmem]` is a project dep (see Background): `langgraph dev` must run in the same venv as `langchain`, so we install it via `uv sync` and invoke it with `uv run langgraph dev`.

- [ ] **Step 3: Write `langgraph.json`**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/langgraph.json`:

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/{{ cookiecutter.project_slug }}/agent.py:graph"
  },
  "env": "./.env"
}
```

`"dependencies": ["."]` tells `langgraph dev` to install the current project (so it can import the graph). `"env": "./.env"` makes `langgraph dev` load `.env` before importing the graph, so the bridge in `agent.py` sees the variables.

- [ ] **Step 4: Write `.env.example`**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example`:

```bash
# --- Pick ONE pair ----------------------------------------------------------
# init_chat_model(..., model_provider="openai") reads OPENAI_*. The bridge at
# the top of agent.py copies AGENTSEEK_* over when only the latter are set.
OPENAI_API_KEY=
OPENAI_API_BASE=

AGENTSEEK_API_KEY=
AGENTSEEK_API_BASE=
```

The `LANGGRAPH_PORT` and `FRONTEND_PORT` env vars live in `frontend/.env.example` only — they're read by Vite's `loadEnv`. The backend's port is passed on the `langgraph dev --port` command line in the generated README, not from `.env`.

- [ ] **Step 5: Write `.gitignore`**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.gitignore`:

```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.egg-info/
build/
dist/

# langgraph dev in-memory checkpoint state
.langgraph_api/

# Node
node_modules/
frontend/dist/

# Env
.env
```

- [ ] **Step 6: Create the empty package marker**

```bash
touch 'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py'
```

The file must exist (empty is fine) so `langgraph dev` can import `{{slug}}.agent` as a package member.

- [ ] **Step 7: Write `agent.py`**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/agent.py`:

```python
"""LangChain `create_agent` graph, served by `langgraph dev`.

This module is pure LangChain — no agentseek dependency. It mirrors what a
developer would write by following the LangChain docs:

  https://docs.langchain.com/oss/python/langchain/quickstart

The 4-line ``AGENTSEEK_*`` → ``OPENAI_*`` bridge is a convenience for users
whose ``.env`` only carries agentseek-style credentials; ``init_chat_model``
itself only reads the ``OPENAI_*`` pair.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

load_dotenv()

# .env bridge: prefer pre-set OPENAI_* but accept AGENTSEEK_* as a fallback.
if os.getenv("AGENTSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AGENTSEEK_API_KEY"]
if os.getenv("AGENTSEEK_API_BASE") and not os.getenv("OPENAI_API_BASE"):
    os.environ["OPENAI_API_BASE"] = os.environ["AGENTSEEK_API_BASE"]

model = init_chat_model("{{ cookiecutter.default_model }}", model_provider="openai")

graph = create_agent(
    model=model,
    tools=[],
    system_prompt="""{{ cookiecutter.system_prompt }}""",
)
```

Notes on the Jinja rendering:
- `"{{ cookiecutter.default_model }}"` renders to the literal string `"deepseek-ai/DeepSeek-V3"` (default), with the quotes preserved. The `model_provider="openai"` kwarg is more readable than the `"openai:..."` prefix form and the runtime behavior is identical.
- `"""{{ cookiecutter.system_prompt }}"""` uses a triple-quoted Python string defensively — the default prompt contains an em-dash which is safe, but any user who runs `agentseek create` interactively and types a prompt containing a `"` would otherwise get a `SyntaxError` at `langgraph dev` boot. Triple-quoting absorbs single double-quotes safely.

- [ ] **Step 8: Run the render-check to confirm the new template renders cleanly**

```bash
cd /Users/zhl/workspaces/agentseek
uv run --package agentseek-cli pytest contrib/agentseek-cli/tests/test_templates_render.py -v
```

Expected: 6 PASS lines (1 sanity + 5 templates: the four existing + `langchain/markdown-messages`). Runtime under 5 seconds.

If `langchain/markdown-messages` does not appear in the parametrize ids, the discovery missed it — check `cookiecutter.json` is present and the directory is exactly `templates/langchain/markdown-messages/`.

- [ ] **Step 9: End-to-end render + smoke-test the backend against SiliconFlow**

This step proves the generated Python project actually boots and serves a response from the real model. Do this **before** committing — if the backend doesn't run, no amount of frontend work in later tasks will save the template.

Export the live SiliconFlow credentials (see Background):

```bash
export AGENTSEEK_API_KEY="sk-rugfpsgkcnslyqaumbuugsluxnvreemaczqnyiqejgpbgoeu"
export AGENTSEEK_API_BASE="https://api.siliconflow.cn/v1"
```

Render the template into a clean scratch dir:

```bash
rm -rf /tmp/agentseek-e2e && mkdir -p /tmp/agentseek-e2e
cd /tmp/agentseek-e2e
uv run --project /Users/zhl/workspaces/agentseek --package agentseek-cli \
  agentseek create langchain/markdown-messages --no-input
```

Expected: `/tmp/agentseek-e2e/markdown_messages_agent/` containing `pyproject.toml`, `langgraph.json`, `.env.example`, `.gitignore`, `src/markdown_messages_agent/agent.py`. The `frontend/` directory does not exist yet (lands in Task 2).

Sync deps. If PyPI is slow or refuses connections, fall back to the Tsinghua mirror:

```bash
cd /tmp/agentseek-e2e/markdown_messages_agent
uv sync \
  || UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv sync
```

Copy and populate `.env` with the exported creds:

```bash
cp .env.example .env
sed -i.bak "s|^AGENTSEEK_API_KEY=.*|AGENTSEEK_API_KEY=${AGENTSEEK_API_KEY}|" .env
sed -i.bak "s|^AGENTSEEK_API_BASE=.*|AGENTSEEK_API_BASE=${AGENTSEEK_API_BASE}|" .env
rm .env.bak
```

Boot `langgraph dev` in the project venv (NOT via a global tool — see Background):

```bash
uv run langgraph dev --port 2024 --no-browser > /tmp/agentseek-e2e/langgraph.log 2>&1 &
LANGGRAPH_PID=$!
sleep 12  # langgraph dev needs ~10s to import the graph and open the port
```

Verify the server is healthy:

```bash
curl -sS http://127.0.0.1:2024/ok
# Expected exactly: {"ok":true}
```

If `curl` hangs or errors, run `tail -40 /tmp/agentseek-e2e/langgraph.log` and look for the first line containing `error` or `Error`. The most common failures:
- `ModuleNotFoundError: No module named 'langchain'` → `langgraph-cli` was installed in a venv that doesn't have `langchain`. Confirm you ran it with `uv run` from the project dir, not from a global install.
- Graph import error: `cat .env` to confirm both AGENTSEEK_* values are populated.

Invoke the agent against the real model. Use `/runs/wait` (the synchronous endpoint that returns the final state):

```bash
curl -sS -X POST 'http://127.0.0.1:2024/runs/wait' \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"type": "human", "content": "Reply in one short markdown sentence with a bold word."}
      ]
    }
  }' | head -c 2000
```

Expected: a JSON object `{"messages": [...]}` whose final element has `"type":"ai"` and a non-empty `"content"`. The `model_name` field may echo `deepseek-ai/DeepSeek-V3` verbatim or may surface the provider's normalized form (`deepseek-chat`, etc.) — don't assert on it. The pass criterion is just: an `ai` message with a non-empty body.

Tear down:

```bash
kill $LANGGRAPH_PID 2>/dev/null
sleep 1
lsof -i :2024 -sTCP:LISTEN 2>/dev/null || echo "port :2024 clear"
```

- [ ] **Step 10: Commit**

```bash
cd /Users/zhl/workspaces/agentseek
git add templates/langchain/markdown-messages/cookiecutter.json \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/pyproject.toml' \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/langgraph.json' \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example' \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.gitignore' \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/__init__.py' \
  'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/agent.py'
git commit -m "feat(templates): add langchain/markdown-messages backend (pure)

Python create_agent served via 'langgraph dev'. No agentseek dependency.
Uses init_chat_model with the standard AGENTSEEK_* → OPENAI_* env bridge
from templates/CONTRIBUTING.md so users with either credential pair work.

langgraph-cli[inmem] is a project dependency, not a global tool: the
in-mem dev server runs the graph inside its own venv (it does NOT install
langgraph.json's 'dependencies' array — that's only used by 'langgraph
build'), so it has to live alongside langchain in the project venv.

Frontend follows in the next commit."
```

Do **not** commit `/tmp/agentseek-e2e/*` or any `.env` — they live outside the repo.

---

## Task 2: Frontend skeleton

Stand up the Vite + React + TS frontend shell — just enough that `npm install` and `npm run build` succeed. The `useStream` hook + markdown rendering land in Task 3 so each task is independently verifiable.

**Files:**
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/package.json`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/tsconfig.json`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/tsconfig.node.json`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/vite.config.ts`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/index.html`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/.env.example`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/.gitignore`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/main.tsx`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/App.tsx` (placeholder; full UI in Task 3)
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/styles.css`
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/vite-env.d.ts`

- [ ] **Step 1: Write `frontend/package.json`**

Versions are pinned to what works as of plan date (2026-05-28). **`@langchain/react` uses `~0.3.5`** — see "Why the `@langchain/react` pin" in Background. Newer versions (`^1.0`) break against `langgraph-cli[inmem] 0.4.x` because they call `POST /threads/{tid}/commands`, an endpoint not present in `langgraph-api < 0.9.0`. `0.3.5` pins `@langchain/langgraph-sdk@1.8.10` transitively, which uses the supported `/threads/{tid}/runs/stream` endpoint; the `~` allows same-line 0.3.x patches but blocks the 0.4.0+ jump.

```json
{
  "name": "{{ cookiecutter.project_slug }}-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@langchain/core": "^1.1.44",
    "@langchain/react": "~0.3.5",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.10.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.6.3",
    "vite": "^5.4.11"
  }
}
```

`@types/node` is needed because `vite.config.ts` calls `process.cwd()` — without it, `tsc -b` fails with "Cannot find name 'process'".

- [ ] **Step 2: Write `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Write `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "types": ["node"]
  },
  "include": ["vite.config.ts"]
}
```

`"types": ["node"]` activates `@types/node` for `vite.config.ts` only (kept out of the app code's tsconfig).

- [ ] **Step 4: Write `frontend/vite.config.ts`**

The port comes from `FRONTEND_PORT` at dev time (Vite reads it via `loadEnv`) and falls back to the cookiecutter default. Keeps the two-process startup hands-off — users can edit `.env`, not config code.

```ts
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const port = Number(env.FRONTEND_PORT ?? "{{ cookiecutter.frontend_port }}");
  return {
    plugins: [react()],
    server: { port, strictPort: true },
  };
});
```

- [ ] **Step 5: Write `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ cookiecutter.project_name }}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Write `frontend/.env.example`**

```bash
VITE_LANGGRAPH_API_URL=http://127.0.0.1:{{ cookiecutter.langgraph_port }}
FRONTEND_PORT={{ cookiecutter.frontend_port }}
```

- [ ] **Step 7: Write `frontend/.gitignore`**

```gitignore
node_modules/
dist/
.env
.env.local
```

- [ ] **Step 8: Write `frontend/src/main.tsx`**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 9: Write `frontend/src/App.tsx` (placeholder)**

The full `useStream`-driven UI lands in Task 3. This placeholder lets `tsc -b && vite build` succeed in this task without dragging in unfinished hook wiring.

```tsx
export default function App() {
  return (
    <main>
      <h1>{{ cookiecutter.project_name }}</h1>
      <p>Wiring up <code>useStream</code> in Task 3.</p>
    </main>
  );
}
```

- [ ] **Step 10: Write `frontend/src/styles.css`**

Minimal — typography + a max-width content column. Task 3 will add markdown-element styles (tables, code blocks). Keeping styles here (not Tailwind) so the template ships with zero CSS tooling.

```css
:root {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 1.5;
  color-scheme: light dark;
}

body {
  margin: 0;
  background: #f7f7f8;
  color: #1f1f1f;
}

main {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem 1rem 6rem;
}

code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.1em 0.35em;
  border-radius: 3px;
  font-size: 0.95em;
}

@media (prefers-color-scheme: dark) {
  body { background: #1c1c1e; color: #f2f2f7; }
  code { background: rgba(255, 255, 255, 0.08); }
}
```

- [ ] **Step 11: Write `frontend/src/vite-env.d.ts`**

```ts
/// <reference types="vite/client" />
```

- [ ] **Step 12: Run the render-check**

```bash
cd /Users/zhl/workspaces/agentseek
uv run --package agentseek-cli pytest contrib/agentseek-cli/tests/test_templates_render.py -v
```

Expected: 6 PASS. The `frontend/package.json` JSON-validity assertion in the test now exercises this template's frontend.

- [ ] **Step 13: End-to-end render + frontend build**

Re-render into the scratch dir and confirm the frontend toolchain installs and builds:

```bash
rm -rf /tmp/agentseek-e2e && mkdir -p /tmp/agentseek-e2e
cd /tmp/agentseek-e2e
uv run --project /Users/zhl/workspaces/agentseek --package agentseek-cli \
  agentseek create langchain/markdown-messages --no-input

cd /tmp/agentseek-e2e/markdown_messages_agent/frontend
npm install
npm run build
```

Expected from `npm run build`: a `dist/` directory with `index.html` and the React bundle. Build time under 30 seconds. Warnings about source maps are fine; **errors are not**.

If `npm install` is slow or fails because the npm registry is unreachable, retry with a mirror:

```bash
npm install --registry=https://registry.npmmirror.com
```

(Do not commit a `.npmrc` to the template — the mirror is a debug workaround, not a default.)

- [ ] **Step 14: Commit**

```bash
cd /Users/zhl/workspaces/agentseek
git add 'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/'
git commit -m "feat(templates): add markdown-messages frontend skeleton

Vite + React 18 + TS shell. Pinned @langchain/react@~0.3.5 (the 1.x
line requires a /threads/{tid}/commands endpoint that
langgraph-cli[inmem] 0.4.x doesn't ship — pinning here keeps useStream
on the supported /runs/stream path). 0.3.5 pins
@langchain/langgraph-sdk to exact 1.8.10 transitively. Placeholder
App component renders 'Wiring up useStream in Task 3.' so 'npm run
build' passes before the actual hook lands."
```

---

## Task 3: `useStream` + markdown rendering

Replace the placeholder `App.tsx` with the real chat UI: an input box, a streaming message list, each AI message rendered through `react-markdown` + `remark-gfm`. Verified end-to-end by running the backend from Task 1 + the frontend from Task 2, opening the page in a real browser via the `superpowers:dev-browser` skill, sending "show me a table of three colors", and confirming the response renders as an HTML table.

**Files:**
- Modify: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/App.tsx` (replace placeholder)
- Modify: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/styles.css` (add markdown element styles)

- [ ] **Step 1: Replace `App.tsx` with the streaming chat UI**

Overwrite `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/App.tsx` with:

```tsx
import { FormEvent, useState } from "react";
import { useStream } from "@langchain/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = { id?: string; type: string; content: unknown };

function messageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) =>
        typeof part === "string"
          ? part
          : typeof part === "object" && part !== null && "text" in part
            ? String((part as { text: unknown }).text ?? "")
            : "",
      )
      .join("");
  }
  return "";
}

export default function App() {
  const apiUrl =
    import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://127.0.0.1:{{ cookiecutter.langgraph_port }}";

  const stream = useStream<{ messages: Message[] }>({
    apiUrl,
    assistantId: "agent",
  });

  const [input, setInput] = useState("");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || stream.isLoading) return;
    setInput("");
    stream.submit({ messages: [{ type: "human", content: text }] });
  }

  return (
    <main>
      <h1>{{ cookiecutter.project_name }}</h1>

      <section className="chat" aria-label="Conversation">
        {stream.messages.length === 0 && (
          <p className="hint">Try: <em>"show me a table of three colors with hex codes"</em></p>
        )}
        {stream.messages.map((msg, i) => (
          <article key={msg.id ?? i} className={`msg msg--${msg.type}`}>
            <header className="msg__role">{msg.type}</header>
            <div className="msg__body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {messageText(msg.content)}
              </ReactMarkdown>
            </div>
          </article>
        ))}
        {stream.isLoading && <p className="hint">…thinking</p>}
        {stream.error ? <p className="error">{String(stream.error)}</p> : null}
      </section>

      <form className="composer" onSubmit={onSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something…"
          disabled={stream.isLoading}
          autoFocus
        />
        <button type="submit" disabled={stream.isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </main>
  );
}
```

Notes on the design choices:
- **`messageText()` helper.** LangChain messages can carry `content` as either a plain string or an array of parts (`{type:"text", text:"..."}`). We collapse to a string so `<ReactMarkdown>` gets what it expects. Anything else (tool calls, images) renders as empty — out of scope for this template.
- **`stream.submit({ messages: [...] })`.** `useStream` appends to existing state; we only send the new human turn, not the whole history.
- **`VITE_LANGGRAPH_API_URL` fallback.** If the user forgot `.env`, the literal cookiecutter port still works on localhost. The `.env` value wins when present.

- [ ] **Step 2: Append markdown styles to `styles.css`**

Append (not replace) to `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/styles.css`:

```css
/* Chat layout ---------------------------------------------------------- */
.chat {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 1.5rem 0;
}

.msg {
  border-radius: 8px;
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.03);
}

.msg--human { background: rgba(50, 110, 220, 0.08); }

.msg__role {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.6;
  margin-bottom: 0.25rem;
}

.msg__body > :first-child { margin-top: 0; }
.msg__body > :last-child  { margin-bottom: 0; }

.hint { opacity: 0.7; font-style: italic; }
.error { color: #c0392b; }

.composer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  background: var(--bg, #f7f7f8);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 0.5rem;
}

.composer input {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  font: inherit;
}

.composer button {
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  border: 0;
  background: #1f6feb;
  color: white;
  font: inherit;
  cursor: pointer;
}

.composer button:disabled { opacity: 0.5; cursor: not-allowed; }

/* Markdown elements ---------------------------------------------------- */
.msg__body table {
  border-collapse: collapse;
  margin: 0.5rem 0;
}

.msg__body th,
.msg__body td {
  border: 1px solid rgba(0, 0, 0, 0.15);
  padding: 0.35rem 0.6rem;
  text-align: left;
}

.msg__body pre {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
}

@media (prefers-color-scheme: dark) {
  .msg { background: rgba(255, 255, 255, 0.04); }
  .msg--human { background: rgba(80, 140, 250, 0.15); }
  .composer { background: #1c1c1e; border-top-color: rgba(255, 255, 255, 0.1); }
  .composer input { border-color: rgba(255, 255, 255, 0.15); background: #2a2a2c; color: inherit; }
  .msg__body pre { background: rgba(255, 255, 255, 0.08); }
  .msg__body th, .msg__body td { border-color: rgba(255, 255, 255, 0.15); }
}
```

- [ ] **Step 3: Re-render and rebuild the frontend in /tmp**

```bash
rm -rf /tmp/agentseek-e2e && mkdir -p /tmp/agentseek-e2e
cd /tmp/agentseek-e2e
uv run --project /Users/zhl/workspaces/agentseek --package agentseek-cli \
  agentseek create langchain/markdown-messages --no-input

cd /tmp/agentseek-e2e/markdown_messages_agent/frontend
npm install
npm run build
```

Expected: clean `npm run build` with a `dist/` directory. Build errors here mean the `App.tsx` types or import paths are off — fix and retry before booting the dev servers.

- [ ] **Step 4: Boot the backend (terminal A) and the frontend (terminal B)**

In one shell, boot the backend with creds (same as Task 1 Step 9):

```bash
export AGENTSEEK_API_KEY="sk-rugfpsgkcnslyqaumbuugsluxnvreemaczqnyiqejgpbgoeu"
export AGENTSEEK_API_BASE="https://api.siliconflow.cn/v1"

cd /tmp/agentseek-e2e/markdown_messages_agent
uv sync \
  || UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv sync
cp .env.example .env
sed -i.bak "s|^AGENTSEEK_API_KEY=.*|AGENTSEEK_API_KEY=${AGENTSEEK_API_KEY}|" .env
sed -i.bak "s|^AGENTSEEK_API_BASE=.*|AGENTSEEK_API_BASE=${AGENTSEEK_API_BASE}|" .env
rm .env.bak

uv run langgraph dev --port 2024 --no-browser > /tmp/agentseek-e2e/langgraph.log 2>&1 &
LANGGRAPH_PID=$!
sleep 12
curl -sS http://127.0.0.1:2024/ok  # expect {"ok":true}
```

In another shell, boot the frontend:

```bash
cd /tmp/agentseek-e2e/markdown_messages_agent/frontend
cp .env.example .env
npm run dev > /tmp/agentseek-e2e/vite.log 2>&1 &
VITE_PID=$!
sleep 5
curl -sS http://127.0.0.1:5174 | head -c 200  # expect <!doctype html> ...
```

- [ ] **Step 5: Verify the UI in a real browser using the `dev-browser` CLI**

`dev-browser` is a separate CLI tool (not a superpowers skill — install with `npm install -g dev-browser && dev-browser install` if missing; run `dev-browser --help` for the API). Scripts run in a sandboxed QuickJS runtime with a pre-connected `browser` global that exposes a Playwright `Page`. Use headless mode (`--headless`) so the daemon launches Chromium in the background.

```bash
dev-browser --headless --browser agentseek-md --timeout 180 <<'EOF'
const page = await browser.getPage("md");
await page.goto("http://127.0.0.1:5174", { waitUntil: "networkidle" });
console.log("H1:", await page.locator("h1").first().textContent());

// Probe 1: the canonical table prompt.
await page.fill('input[type="text"]', "show me a table of three colors with hex codes");
await page.click('button[type="submit"]');
await page.waitForSelector('.msg--ai', { timeout: 120000 });
// Stream completion: input clears + button re-disables until next non-empty input.
// Let the stream drain for a few seconds before counting elements.
await new Promise((r) => setTimeout(r, 6000));
const tables = await page.locator('.msg--ai .msg__body table').count();
const rows = await page.locator('.msg--ai .msg__body table tr').count();
console.log("Probe1 tables:", tables, "rows:", rows);
if (tables < 1 || rows < 2) throw new Error("table did not render");

// Probe 2: a fenced code block in a second turn.
await page.fill('input[type="text"]', "show me a fenced code block of Python that prints hello");
await page.click('button[type="submit"]');
await page.waitForFunction(() => document.querySelectorAll('.msg--ai').length >= 2, { timeout: 120000 });
await new Promise((r) => setTimeout(r, 6000));
const codeBlocks = await page.locator('.msg--ai').nth(1).locator('pre code').count();
console.log("Probe2 code blocks:", codeBlocks);
if (codeBlocks < 1) throw new Error("code block did not render");
EOF
```

Expected stdout:
- `H1: Markdown Messages Agent`
- `Probe1 tables: 1 rows: 4` (or more — header row + 3+ data rows)
- `Probe2 code blocks: 1` (or more)

If the table doesn't render (raw markdown text shows instead), the `<ReactMarkdown>` + `remarkGfm` pipeline isn't wired — check the `remarkPlugins={[remarkGfm]}` prop and that `remark-gfm` resolved in `npm install`. If `Probe1` fires the throw with `tables: 0`, dump the body with one more script: `console.log(await page.locator('.msg--ai .msg__body').first().innerHTML())` to see what the model actually returned. If the AI message never arrives and the chat shows `Error: Protocol request failed: 404 Not Found`, the `@langchain/react` pin has drifted off `~0.3.5` — see Background § "Why the `@langchain/react` pin".

- [ ] **Step 6: Tear down**

```bash
kill $VITE_PID $LANGGRAPH_PID 2>/dev/null
sleep 1
lsof -i :2024 -sTCP:LISTEN 2>/dev/null || echo "port :2024 clear"
lsof -i :5174 -sTCP:LISTEN 2>/dev/null || echo "port :5174 clear"
```

- [ ] **Step 7: Commit**

```bash
cd /Users/zhl/workspaces/agentseek
git add 'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/App.tsx' \
        'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/frontend/src/styles.css'
git commit -m "feat(templates): wire useStream + react-markdown in markdown-messages

App.tsx now drives an end-to-end chat against the project's langgraph
dev server. Each message's content runs through ReactMarkdown with
remarkGfm so GFM tables, fenced code blocks, and task lists render
properly. messageText() collapses LangChain's multimodal content array
to a string so the markdown renderer gets what it expects."
```

---

## Task 4: READMEs + `templates/index.json`

Add the two READMEs required by `templates/CONTRIBUTING.md` plus the index entry so `agentseek create --list-templates` shows the new template.

**Files:**
- Create: `templates/langchain/markdown-messages/README.md` (template-level: Inputs table + Generated layout)
- Create: `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/README.md` (generated-project: Setup / Run / Smoke test)
- Modify: `templates/index.json` (add `"langchain/markdown-messages"` entry)

- [ ] **Step 1: Write the template-level README**

Write `templates/langchain/markdown-messages/README.md`:

```markdown
# langchain/markdown-messages — pure LangChain + useStream + react-markdown

Scaffolds a minimal Python + TypeScript template:

- **Backend:** a `langchain.agents.create_agent` graph served by `langgraph dev`.
- **Frontend:** a Vite + React app that streams messages via `@langchain/react`'s `useStream` hook and renders each reply through `react-markdown` (with GFM — tables, fenced code, task lists).

No `agentseek-langchain` / `agentseek-ag-ui` dependency. Mirrors the upstream LangChain quickstart so a developer familiar with LangChain can read this template without learning agentseek wrappers first. See `templates/CONTRIBUTING.md` § "Pure vs agentseek-wrapped templates" for the design rule.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. Defaults to "Markdown Messages Agent". |
| `project_slug` | Python package / directory name. Auto-derived from `project_name`. |
| `author` | Project author shown in `pyproject.toml`. |
| `system_prompt` | System prompt baked into the agent. Default instructs the model to favor markdown formatting. |
| `default_model` | Model id for `init_chat_model`, used as `init_chat_model(<id>, model_provider="openai")`. Defaults to `deepseek-ai/DeepSeek-V3` (works against any OpenAI-compatible endpoint). |
| `langgraph_port` | Backend port for `langgraph dev`. Defaults to `2024`. |
| `frontend_port` | Vite dev-server port. Defaults to `5174`. |

## Generated layout

```
my_project/
├── .env.example                 # OPENAI / AGENTSEEK creds, port defaults
├── .gitignore
├── langgraph.json               # tells `langgraph dev` where the graph lives
├── pyproject.toml               # langchain, langchain-openai, langgraph-cli, dotenv
├── src/my_project/
│   ├── __init__.py
│   └── agent.py                 # load_dotenv + bridge + init_chat_model + create_agent
└── frontend/
    ├── .env.example             # VITE_LANGGRAPH_API_URL, FRONTEND_PORT
    ├── .gitignore
    ├── index.html
    ├── package.json             # @langchain/react@~0.3.5, react-markdown, remark-gfm, vite
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts           # port from FRONTEND_PORT
    └── src/
        ├── App.tsx              # useStream + ReactMarkdown
        ├── main.tsx
        ├── styles.css
        └── vite-env.d.ts
```

## Why DeepSeek-V3 as the default model

The template was validated against SiliconFlow's OpenAI-compatible endpoint. `Qwen/Qwen2.5-7B-Instruct` was too small to produce well-formed markdown tables (output was garbled); `Qwen3.5-9B` is a reasoning model that returns content via `reasoning_content` (which `useStream`/`react-markdown` would render as empty). `deepseek-ai/DeepSeek-V3` produced clean GFM tables and fenced code blocks in both probes. Override with any OpenAI-compatible chat model id when you generate the project.
```

- [ ] **Step 2: Write the generated-project README**

Write `templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/README.md`:

````markdown
# {{ cookiecutter.project_name }}

A LangChain `create_agent` Python graph served by `langgraph dev`, with a Vite + React frontend that streams messages and renders them as markdown.

No agentseek runtime dependency — this is plain LangChain + LangGraph + React.

## Setup

```bash
# 1. Python deps (langchain, langgraph-cli[inmem], etc.)
uv sync

# 2. Frontend deps
npm install --prefix frontend

# 3. Configure credentials. Either fill OPENAI_* directly, or set AGENTSEEK_*
#    and let the .env bridge at the top of src/{{ cookiecutter.project_slug }}/agent.py copy them over.
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env
```

`.env` keys:

- `OPENAI_API_KEY` / `OPENAI_API_BASE` — what `init_chat_model(<id>, model_provider="openai")` actually reads.
- `AGENTSEEK_API_KEY` / `AGENTSEEK_API_BASE` — populated automatically into `OPENAI_*` by the 4-line bridge at the top of `agent.py`. Use this pair if you have agentseek-style creds and want them to "just work".

## Run

Two-terminal dev loop. **Both commands must run from the project root** (the directory containing `pyproject.toml`) — `langgraph dev` resolves `./langgraph.json` and `./.env` relative to your cwd.

**Terminal A — backend:**

```bash
cd {{ cookiecutter.project_slug }}  # from wherever you ran `agentseek create`
uv run langgraph dev --port {{ cookiecutter.langgraph_port }} --no-browser
```

Wait for `Welcome to LangGraph`. The server exposes:
- `GET  /ok` — health probe.
- `POST /threads/<id>/runs/stream` — what `useStream` calls (after first creating a thread via `POST /threads`).
- `GET  /docs` — full OpenAPI of supported endpoints.

**Terminal B — frontend:**

```bash
cd {{ cookiecutter.project_slug }}  # same project root
npm run dev --prefix frontend
```

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Smoke test

Type "show me a table of three colors with hex codes" and press Send. You should see:

1. The user prompt appear in a blue bubble.
2. An AI bubble appear with "…thinking" momentarily.
3. The AI reply renders as a real HTML `<table>` (not raw `| ... |` markdown text) with three rows.

If the table comes back as raw markdown text, the `react-markdown` + `remark-gfm` pipeline isn't running — check `frontend/src/App.tsx`. If the AI reply never arrives and the UI shows an `Error: Protocol request failed: 404`, your `@langchain/react` pin has drifted off `~0.3.5` (newer versions call `POST /threads/<id>/commands`, which the bundled `langgraph-cli[inmem] 0.4.x` server doesn't ship) — see the project's `pyproject.toml` and `frontend/package.json` comments.

## How it's wired

- `src/{{ cookiecutter.project_slug }}/agent.py` — `load_dotenv()`, the `AGENTSEEK_* → OPENAI_*` bridge, `init_chat_model`, and `create_agent`. Exports `graph` for `langgraph.json` to pick up.
- `langgraph.json` — points `agent` at `./src/{{ cookiecutter.project_slug }}/agent.py:graph` and loads `./.env`.
- `frontend/src/App.tsx` — `useStream({ assistantId: "agent", apiUrl: VITE_LANGGRAPH_API_URL })` plus a `ReactMarkdown` render per message.

Author: {{ cookiecutter.author }}
````

- [ ] **Step 3: Add the index entry**

Edit `templates/index.json` and add the new key. Read the current file first:

```bash
cat templates/index.json
```

Add the line `"langchain/markdown-messages": "Pure LangChain create_agent + langgraph dev backend, useStream + react-markdown frontend. No agentseek runtime."` Keep the existing entries. Result:

```json
{
  "deepagents/default": "Local create_deep_agent runnable bound to agentseek-langchain.",
  "langchain/default": "LangChain create_agent + CopilotKit middleware over agentseek-langchain.",
  "langchain/cli-remote": "Remote LangGraph CLI agent bridged via LangGraphClientRunnable.",
  "langchain/markdown-messages": "Pure LangChain create_agent + langgraph dev backend, useStream + react-markdown frontend. No agentseek runtime.",
  "bub/default": "Lightweight Bub agent: agentseek gateway + CopilotKit frontend, no LangChain."
}
```

- [ ] **Step 4: Verify the CLI surfaces the template**

```bash
cd /Users/zhl/workspaces/agentseek
uv run --package agentseek-cli agentseek create --list-templates 2>&1 | grep -A1 markdown-messages
```

Expected: a line containing `langchain/markdown-messages` with the description from `index.json`.

- [ ] **Step 5: Re-run the render-check**

```bash
uv run --package agentseek-cli pytest contrib/agentseek-cli/tests/test_templates_render.py -v
```

Expected: 6 PASS (sanity + 5 templates).

- [ ] **Step 6: Commit**

```bash
git add templates/langchain/markdown-messages/README.md \
        'templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/README.md' \
        templates/index.json
git commit -m "docs(templates): READMEs + index entry for langchain/markdown-messages

Template-level README documents inputs, generated layout, and why the
default model is DeepSeek-V3 (Qwen-7B was too weak, Qwen3.5-9B uses
reasoning_content). Generated-project README walks through the
two-terminal dev loop and the smoke-test commands."
```

---

## Task 5: Full integration verification

Final pass: render with `agentseek create --no-input` into a clean scratch dir, sync, install, run both processes, exercise the UI via `dev-browser`, and confirm everything passes against the *committed* template (no working-tree-only files). This is the regression net for the whole template.

**Files:** none modified.

- [ ] **Step 1: Confirm the working tree is clean for the template**

```bash
cd /Users/zhl/workspaces/agentseek
git status -- templates/langchain/markdown-messages/
```

Expected: empty (everything in the template directory is committed). If there are stray changes, decide whether to commit or revert before continuing — Task 5 must verify what's actually in git, not in your working tree.

- [ ] **Step 2: Render into a clean scratch dir**

```bash
rm -rf /tmp/agentseek-e2e && mkdir -p /tmp/agentseek-e2e
cd /tmp/agentseek-e2e
uv run --project /Users/zhl/workspaces/agentseek --package agentseek-cli \
  agentseek create langchain/markdown-messages --no-input
```

Expected: `/tmp/agentseek-e2e/markdown_messages_agent/` with both backend and frontend trees from the file-structure table.

- [ ] **Step 3: Sync and prep**

```bash
cd /tmp/agentseek-e2e/markdown_messages_agent
uv sync \
  || UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv sync

export AGENTSEEK_API_KEY="sk-rugfpsgkcnslyqaumbuugsluxnvreemaczqnyiqejgpbgoeu"
export AGENTSEEK_API_BASE="https://api.siliconflow.cn/v1"

cp .env.example .env
sed -i.bak "s|^AGENTSEEK_API_KEY=.*|AGENTSEEK_API_KEY=${AGENTSEEK_API_KEY}|" .env
sed -i.bak "s|^AGENTSEEK_API_BASE=.*|AGENTSEEK_API_BASE=${AGENTSEEK_API_BASE}|" .env
rm .env.bak

cd frontend
cp .env.example .env
npm install
npm run build  # cheap regression — fails fast if any frontend file is broken
```

Expected: backend `uv sync` finishes, `npm install` adds ~150 packages, `npm run build` produces `dist/`.

- [ ] **Step 4: Boot both servers**

```bash
cd /tmp/agentseek-e2e/markdown_messages_agent
uv run langgraph dev --port 2024 --no-browser > /tmp/agentseek-e2e/langgraph.log 2>&1 &
LANGGRAPH_PID=$!

cd frontend
npm run dev > /tmp/agentseek-e2e/vite.log 2>&1 &
VITE_PID=$!

sleep 14
curl -sS http://127.0.0.1:2024/ok   # expect {"ok":true}
curl -sS http://127.0.0.1:5174 | head -c 100  # expect <!doctype html>
```

- [ ] **Step 5: Browser-level smoke via `dev-browser`**

Run from any directory:

```bash
dev-browser --headless --browser agentseek-md-e2e --timeout 180 <<'EOF'
const page = await browser.getPage("md");
await page.goto("http://127.0.0.1:5174", { waitUntil: "networkidle" });
console.log("H1:", await page.locator("h1").first().textContent());

// Probe 1: table
await page.fill('input[type="text"]', "show me a table of three colors with hex codes");
await page.click('button[type="submit"]');
await page.waitForSelector('.msg--ai', { timeout: 120000 });
// Wait for stream to finish — input clears, button re-enables only when input is non-empty,
// so detect completion by the count stabilizing for 3 seconds.
await new Promise(r => setTimeout(r, 6000));
const tables = await page.locator('.msg--ai .msg__body table').count();
const rows   = await page.locator('.msg--ai .msg__body table tr').count();
console.log("Probe1 — tables:", tables, "rows:", rows);
if (tables < 1 || rows < 2) throw new Error("table did not render");

// Probe 2: code block in a second turn
await page.fill('input[type="text"]', "show me a fenced code block of Python that prints hello");
await page.click('button[type="submit"]');
await page.waitForFunction(() => document.querySelectorAll('.msg--ai').length >= 2, { timeout: 120000 });
await new Promise(r => setTimeout(r, 6000));
const preCount = await page.locator('.msg--ai').nth(1).locator('pre code').count();
console.log("Probe2 — code blocks:", preCount);
if (preCount < 1) throw new Error("code block did not render");

// Save a screenshot for the record
const path = await saveScreenshot(await page.screenshot({ fullPage: true }), "markdown-messages-e2e-final.png");
console.log("Screenshot:", path);
EOF
```

Expected stdout:
- `H1: Markdown Messages Agent`
- `Probe1 — tables: 1 rows: >= 4`
- `Probe2 — code blocks: >= 1`
- `Screenshot: /Users/.../markdown-messages-e2e-final.png`

If any throw fires, the harness exits non-zero — fix the template, not the test, before declaring victory.

- [ ] **Step 6: Tear down**

```bash
kill $VITE_PID $LANGGRAPH_PID 2>/dev/null
dev-browser stop 2>&1 | tail -1
sleep 1
lsof -i :2024 -i :5174 -sTCP:LISTEN 2>/dev/null || echo "ports clear"
```

- [ ] **Step 7: No commit**

Task 5 is verification, not implementation. There is nothing to commit. If steps 1–5 all pass, the template ships.

---

## Self-Review

**1. Spec coverage.** The plan adds the `langchain/markdown-messages` template called out in the brainstorming summary as "Tier 1 — first wave, smallest possible end-to-end py+ts template". All five tasks produce committed work for that template: backend (Task 1), frontend skeleton (Task 2), real `useStream` + markdown UI (Task 3), READMEs + index entry (Task 4), final integration verification (Task 5). The render-check from the foundation plan (`2026-05-27-template-foundation.md`) automatically picks up the new template via parametrize — verified in Task 1 Step 8 and again in Task 4 Step 5.

**2. Placeholder scan.** Searched for "TBD", "TODO", "implement later", "add appropriate", "similar to Task". None present. Every code block in every step is complete content to be written. Every command has expected output. The two design decisions that drove iteration during the plan's drafting — the `langgraph-cli` global-tool dead-end and the `@langchain/react` 1.x incompatibility with `langgraph-api 0.8.x` — are explained in the Background and pinned in the actual cookiecutter content.

**3. Type consistency.** `messageText` in `App.tsx` operates on the same `Message` type declared in the same file. `cookiecutter.langgraph_port` (default `"2024"`) is used identically in `langgraph.json`, the backend `.env.example`, the frontend `.env.example`, and the `App.tsx` fallback. `cookiecutter.frontend_port` (default `"5174"`) is used identically in `vite.config.ts`, the frontend `.env.example`, and the generated README. Variable naming matches between tasks: `assistant_id: "agent"` in Task 1's curl matches `assistantId: "agent"` in Task 3's `useStream` call (langgraph's REST snake_case vs JS camelCase is intentional — same value).

**4. Verification matches reality.** Tasks 1, 2, 3 were physically run end-to-end during plan-drafting against the real SiliconFlow endpoint. Task 1's `curl /runs/wait` returned an actual AI message. Task 2's `npm run build` produced a real `dist/`. Task 3's `dev-browser` script produced the rendered table and code block visible in the screenshot. Task 5 just re-runs those exact same commands against the committed tree as the regression net.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-28-langchain-markdown-messages.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task with the implementer/spec-reviewer/quality-reviewer prompts from `superpowers:subagent-driven-development`. Each task is independently verifiable and the e2e in Task 5 catches anything an implementer missed.

**2. Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, with batch checkpoints.

Which approach?



