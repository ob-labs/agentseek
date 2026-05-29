---
title: 02 — Build your first harness app
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - contrib/agentseek-cli/pyproject.toml
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/README.md
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
  - templates/bub/default/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/dev.py
  - docs/index.md
---

# Build your first harness app

> **You will:** generate a new project from the `bub/default` template, install it as a
> standalone Python package, and run an agent that *you* own end to end — frontend, gateway,
> and configuration.
> **You need:** Python 3.12+, [uv](https://docs.astral.sh/uv/), and a model provider API
> key. Node.js + npm are required only if you also want the bundled CopilotKit frontend; the
> tutorial calls that out when it matters.

This tutorial spans the two paths from the overview. It starts with
`agentseek create` from the **project lifecycle CLI** (`agentseek-cli`), then
switches into the generated project's own `uv sync`, which resolves the **harness**
there. That generated project is what you keep editing afterward. Tutorial 03 builds on
it, so do not delete it at the end.

## 1. Generate a project from a template

agentseek ships a handful of starter templates under `templates/`. Each combines a
framework choice (`bub`, `langchain`, `deepagents`) with a flavour (`default`, `cli-remote`,
…). The catalogue is one command away:

```bash
uv run agentseek create --list-templates
```

```text title="expected output"
Available deepagents templates:
  default  Local create_deep_agent runnable bound to agentseek-langchain.
Available langchain templates:
  cli-remote  Remote LangGraph CLI agent bridged via LangGraphClientRunnable.
  default     LangChain create_agent + CopilotKit middleware over agentseek-langchain.
Available bub templates:
  default  Lightweight Bub agent: agentseek gateway + CopilotKit frontend, no LangChain.
```

This tutorial uses **`bub/default`** because it is the lightest path through the harness
(no LangChain in the dependency graph, no remote runtime). Choose a working directory
*outside* this checkout — the template generates a peer project, not a subfolder.

The `create` command belongs to `agentseek-cli`
(`contrib/agentseek-cli/pyproject.toml:17-21`). This tutorial calls it from the synced repo
because tutorial 01 already prepared that environment; the standalone Path A equivalent is
`uv tool install agentseek-cli`.

```bash
mkdir -p ~/projects && cd ~/projects
uv run --project ~/code/agentseek agentseek create bub --template default --no-input
```

`--no-input` accepts every default in the template's `cookiecutter.json`, which gives you a
project called `my_bub_agent`. Drop the flag if you want the interactive prompts (project
name, ports, author).

Substitute `~/code/agentseek` with wherever you cloned the agentseek checkout in tutorial 01.

The command prints little on success. Verify the layout:

```bash
ls -a my_bub_agent
```

```text title="expected output"
Dockerfile   .env.example   frontend   pyproject.toml   README.md   src
```

You now own a real Python package: its `pyproject.toml` lists `agentseek` and
`agentseek-ag-ui` as dependencies, its `src/my_bub_agent/dev.py` is a supervisor that
spawns the gateway plus the frontend, and its `frontend/` directory is a CopilotKit Next.js
app. The template README also lives in the project root.

## 2. Install the project's own dependencies

The generated project is a normal `uv` project. From the project root:

```bash
cd my_bub_agent
uv sync
```

This creates a `.venv/` inside `my_bub_agent/` (not inside the agentseek checkout) and
installs `agentseek`, `agentseek-ag-ui`, and the other listed dependencies. If you generated
the project from a local source checkout, `pyproject.toml` will already point to it via
`[tool.uv.sources]` — see `../reference/templates.md` for the full table.

## 3. Configure the model

The template ships an `.env.example`. Copy it.

```bash
cp .env.example .env
```

The defaults you get (verbatim from the template):

```text title=".env.example"
AGENTSEEK_MODEL=openai:gpt-4o-mini
AGENTSEEK_API_KEY=
AGENTSEEK_API_BASE=
AGENTSEEK_STREAM_OUTPUT=true
AGENTSEEK_AG_UI_PORT=8088
FRONTEND_PORT=5173
COPILOTKIT_PORT=4000
AGENTSEEK_AG_UI_AGENT_URL=http://127.0.0.1:8088/agent
```

Fill in `AGENTSEEK_API_KEY` (and `AGENTSEEK_API_BASE` if you are not on OpenAI). Replace the
model if you want — `openrouter:free`, `openai:qwen-plus`, etc. The variable names are the
same set that the CLI uses, because the template depends on the same agentseek
distribution. The full reference is at `../reference/environment.md`.

## 4. Run the gateway

The template's `dev.py` supervisor expects the CopilotKit frontend to be present.
For a backend-only smoke test, skip the frontend bits and run the gateway directly:

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

Instead, run the following from the repository checkout to confirm the command's shape:

```bash
uv run agentseek gateway --help
```

```text title="expected output"
 Usage: agentseek gateway [OPTIONS]

 Start message listeners(like telegram).

 --enable-channel        TEXT  Channels to enable for CLI (default: all)
 --help                        Show this message and exit.
```

The full dev path (frontend + gateway) requires `npm`. From the project root:

```bash title="not executed in this run"
npm install --prefix frontend
uv run agentseek run --no-browser
```

`agentseek run` (provided by the `agentseek-cli` contrib package, see
`../reference/cli.md`) wraps the supervisor in `src/my_bub_agent/dev.py`. It launches the
gateway on `AGENTSEEK_AG_UI_PORT` (default `8088`) and the CopilotKit-backed frontend on
`FRONTEND_PORT` (default `5173`). Once both processes report ready, open
`http://127.0.0.1:5173` in a browser and send a chat turn.

## 5. Confirm the agent is yours

Open `src/my_bub_agent/dev.py` and read the supervisor (lines 88–119): the gateway is
spawned with `agentseek gateway --enable-channel ag-ui`, the frontend with `npm run dev`,
and both are reaped on `SIGINT`/`SIGTERM`. Nothing about that process is locked to the
agentseek repository — you can edit the file, change the channels, swap the frontend, or
delete the frontend entirely and call the gateway from elsewhere. The harness is yours.

The model-routing decisions live in `agentseek-ag-ui` (a contrib package) and in the
`agentseek` distribution itself; see `../explanation/runtime-data-model.md` for how a turn
flows from a channel through the runtime to the model.

## What you have now

- A standalone project directory (`~/projects/my_bub_agent` if you followed the defaults)
  with its own `pyproject.toml`, `.venv/`, and `src/` layout.
- A populated `.env` pointing at a real model.
- Verified shapes for `agentseek create` and `agentseek gateway`.
- A clear sense that `agentseek create` is just the entry step: after `uv sync`, this
  generated project — not the cloned `agentseek` repo — is the harness environment you keep
  editing.

## Where to go next

- Add a local skill and an MCP server to the project you just generated:
  `03-add-a-skill-and-mcp.md`.
- Switch model providers without breaking the project: `../how-to/configure-model.md`.
- Look up every flag for `agentseek create`, `agentseek gateway`, and `agentseek run`:
  `../reference/cli.md`.
- See the full list of templates and what each ships: `../reference/templates.md`.
- Run the same project under Docker Compose: `../how-to/run-with-docker-compose.md`.
