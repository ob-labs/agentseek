# AgentSeek API Runtime Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every AgentSeek-generated backend start through `uv run agentseek-api dev`, with verified CLI, template, and runtime behavior.

**Architecture:** Keep AgentSeek lifecycle TOML as the orchestration contract. Templates declare the AgentSeek API process and health URL; AgentSeek manages checks, env, cwd, subprocess supervision, and frontend ordering. AgentSeek API remains the runtime and reads `agentseek.json`, `langgraph.json`, or explicit `AGENTSEEK_GRAPHS` without invoking LangGraph CLI.

**Tech Stack:** Python, Typer, pytest, TOML lifecycle specs, Cookiecutter templates, uv lockfiles, FastAPI/Uvicorn.

## Global Constraints

- Runtime startup must use `uv run agentseek-api dev`.
- Current user modifications must be preserved.
- LangGraph Python libraries/config compatibility may remain; LangGraph CLI startup may not.
- Secrets remain placeholders only in `.env.example` files.
- Verify before claiming completion.

---

### Task 1: Establish AgentSeek lifecycle runtime contract

**Files:**
- Modify: `agentseek/src/agentseek/cli/lifecycle/core.py`
- Modify: `agentseek/src/agentseek/cli/lifecycle/spec.py` and related lifecycle JSON rendering code identified by tests
- Test: `agentseek/tests/cli_commands/test_lifecycle.py`

- [ ] **Step 1: Add failing tests** for backend runtime/tool checks, human info, JSON info, dry-run command, and live doctor using the same configured URL.
- [ ] **Step 2: Run focused lifecycle tests** with `uv run pytest tests/cli_commands/test_lifecycle.py -q` and confirm the new assertions fail.
- [ ] **Step 3: Implement the smallest lifecycle changes** so `agentseek-api` is checked as an executable, backend runtime is rendered without secrets, and the declared command remains the only process command.
- [ ] **Step 4: Add regression coverage** for missing executable, missing graph config, port collision/startup failure, and subprocess cleanup while preserving existing user edits.
- [ ] **Step 5: Run focused AgentSeek tests** and inspect the diff.

### Task 2: Validate and, only if needed, fix AgentSeek API CLI/config behavior

**Files:**
- Inspect/modify: `agentseek-api/src/agentseek_api/cli.py`
- Inspect/modify: `agentseek-api/src/agentseek_api/settings.py` and config loader modules only if required
- Test: `agentseek-api/tests/unit/test_cli.py`, `agentseek-api/tests/unit/test_graph_manifest.py`, relevant integration tests

- [ ] **Step 1: Run existing CLI/config tests** covering `dev`, `--config`, env files, graph loading, host, port, and reload.
- [ ] **Step 2: Run the CLI help and a minimal temporary graph project** with `uv run agentseek-api dev --no-browser --no-reload`, custom host/port, and explicit config.
- [ ] **Step 3: If a required behavior fails, add a focused failing test** before changing implementation.
- [ ] **Step 4: Implement only confirmed runtime gaps**, ensuring the process starts uvicorn directly and never shells out to `langgraph dev`.
- [ ] **Step 5: Run the focused runtime test set and record supported flag mapping (`--reload` versus `--no-reload`).

### Task 3: Migrate and verify the smallest template

**Files:**
- Modify: `agentseek-templates/templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml`
- Modify: `agentseek-templates/templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/pyproject.toml`
- Modify: generated/template `langgraph.json`, `.env.example`, README, tests as present
- Regenerate: the template's `uv.lock` using uv

- [ ] **Step 1: Inspect the existing user edits and add tests** asserting the generated backend command, dependency, config, URL, and docs.
- [ ] **Step 2: Generate a project from the minimal template** in an isolated temporary directory and run `uv sync`/lock regeneration.
- [ ] **Step 3: Run `agentseek info`, `agentseek doctor`, and `agentseek dev --dry-run`; confirm output contains `agentseek-api` and no LangGraph CLI command.
- [ ] **Step 4: Start the backend, run `agentseek doctor --live`, and exercise health, assistant, thread/run, and streaming endpoints as supported by the template.
- [ ] **Step 5: Fix only template or runtime defects exposed by this validation, then rerun the complete minimal-template flow.

### Task 4: Batch-migrate all AgentSeek templates

**Files:**
- Modify every affected file under `agentseek-templates/templates/`, including lifecycle TOML, `pyproject.toml`, lockfiles, graph config, env examples, scripts, tests, and current README docs
- Modify: template registry/catalog files identified by the scan

- [ ] **Step 1: Produce a classified scan** excluding generated `node_modules` noise and list every occurrence of `langgraph dev`, `uv run langgraph dev`, `langgraph-cli`, and `langgraph_api`.
- [ ] **Step 2: Update each backend lifecycle command** to the supported `agentseek-api dev` flags, retaining port/host/cwd/env/reload semantics.
- [ ] **Step 3: Add a consistent `agentseek-api` dependency** to every backend template that starts a local backend, preserving required LangGraph/LangChain packages.
- [ ] **Step 4: Regenerate each affected lockfile** with uv and verify Python/version compatibility.
- [ ] **Step 5: Update env examples, graph configs, frontend backend URLs, scripts, tests, and current docs.
- [ ] **Step 6: Generate each migrated template and run its static lifecycle checks and dry-run; group only templates that share an identical validated contract.

### Task 5: End-to-end and cross-repository verification

**Files:**
- Modify only tests/docs needed for failures discovered in Tasks 1–4.

- [ ] **Step 1: Run AgentSeek CLI coverage** for `dev --dry-run`, `info`, `info --json`, `doctor`, and `doctor --live`, including missing dependency, port conflict, health failure, and child-process failure cases.
- [ ] **Step 2: Run AgentSeek API unit/integration coverage** for CLI startup, config precedence, graph loading, health, threads/runs, streaming, auth/MCP/store/A2A/CORS paths used by migrated templates.
- [ ] **Step 3: Run generated-template smoke tests** covering create, info, doctor, dry-run, startup, live doctor, graph call, streaming, thread/run, frontend URL, and reload where feasible.
- [ ] **Step 4: Run a final classified repository scan** and ensure no current startup path contains `langgraph dev`, `uv run langgraph dev`, or a requirement on `langgraph-cli`.
- [ ] **Step 5: Review all three git diffs and status**, preserve unrelated user files, and report tests, template count/list, runtime changes, remaining LangGraph dependencies, and unresolved issues.
