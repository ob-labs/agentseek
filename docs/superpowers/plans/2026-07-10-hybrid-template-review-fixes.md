# Hybrid Template Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PR #123 mergeable and ensure the generated hybrid RAG template's documented setup, provider switching, remote access, user-image ingestion, comparison behavior, and smoke proof work as described.

**Architecture:** Keep `langchain-oceanbase` as the only seekdb integration and preserve LangChain instrumentation for Phoenix. Repair configuration at the template boundary, persist user images under managed media storage, retrieve one candidate set for all comparison modes, and expand rendered-project smoke coverage without requiring hosted-provider secrets.

**Tech Stack:** Cookiecutter, AgentSeek lifecycle TOML, Python 3.12+, LangChain/LangGraph, `langchain-oceanbase`, FastAPI, React/Vite/TypeScript, pytest, GitHub Actions.

## Global Constraints

- Public provider configuration uses `AGENTSEEK_MODEL_PROVIDER`, `AGENTSEEK_MODEL`, `AGENTSEEK_API_KEY`, and `AGENTSEEK_API_BASE`.
- SiliconFlow remains the default OpenAI-compatible endpoint for chat, text/image embeddings, and VLM captions.
- Persistence and vector retrieval continue through `langchain-oceanbase` `OceanbaseVectorStore`; do not import or call `pyseekdb` directly.
- Lab, Compare, and Ask remain LangChain/LangGraph-instrumented for Phoenix.
- Default servers bind to loopback; documented `LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0` remote development must work.
- Preserve the user's untracked `artifacts/` directory.

---

### Task 1: Integrate Current Main

**Files:**
- Modify: `tests/cli_commands/test_templates_render.py`

**Interfaces:**
- Consumes: upstream `f23416d` dependency task normalization.
- Produces: a conflict-free branch containing both `language_instruction_templates` and `dependency_sync_templates` assertions.

- [ ] **Step 1: Merge `origin/main`**

Run: `git merge --no-edit origin/main`

Expected: one conflict in `tests/cli_commands/test_templates_render.py`.

- [ ] **Step 2: Resolve the conflict**

Keep both collections and both helper-based content-builder checks. Include `langchain/agentic-rag-hybrid` in the sync-task verification set.

- [ ] **Step 3: Verify the merged baseline**

Run: `uv run python -m pytest tests/cli_commands/test_templates_render.py -q`

Expected: all render and lifecycle cases pass.

### Task 2: Repair Configuration, Networking, and Prompt Contract

**Files:**
- Modify: `tests/cli_commands/test_agentic_rag_hybrid_template.py`
- Modify: `tests/cli_commands/test_templates_render.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/tests/test_agent_tool.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/frontend/package.json`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/langgraph.json`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/agent.py`
- Modify: `templates/langchain/agentic-rag-hybrid/cookiecutter.json`

**Interfaces:**
- Consumes: lifecycle alias resolution and Vite `server.host` from `vite.config.ts`.
- Produces: canonical-key readiness, native-provider credential precedence, working remote binding/CORS, and a same-language default prompt.

- [ ] **Step 1: Write failing tests**

Add assertions that `SILICONFLOW_API_KEY` is not a separate lifecycle requirement, `AGENTSEEK_API_KEY` alone satisfies environment checks, the Vite script has no hard-coded host, CORS accepts the documented development origins, native provider keys win for native adapters, and the hybrid prompt includes `Answer in the same language as the user's question.`

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run python -m pytest tests/cli_commands/test_agentic_rag_hybrid_template.py tests/cli_commands/test_templates_render.py -q`

Run from a rendered project: `uv run python -m pytest tests/test_agent_tool.py -q`

Expected: failures identify the duplicate key, host override, CORS restriction, provider precedence, and missing prompt sentence.

- [ ] **Step 3: Implement minimal fixes**

Remove the duplicate lifecycle requirement, let Vite use `FRONTEND_HOST`, allow development CORS origins required by remote binding, prefer `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` for native adapters, and append the same-language instruction to the default prompt.

- [ ] **Step 4: Run tests and verify GREEN**

Repeat the focused commands; expected: pass.

### Task 3: Make User Images Servable and Upload Ingestion Non-Blocking

**Files:**
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/store.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/routes.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/tests/test_hybrid.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/tests/test_routes.py`

**Interfaces:**
- Consumes: `Settings.media_data_dir` and `_servable_image_path` managed-root validation.
- Produces: `_managed_image_path(image_path, image_id) -> Path` behavior and a synchronous upload endpoint.

- [ ] **Step 1: Write failing tests**

Assert that directory ingestion copies each source image to `MEDIA_DATA_DIR/images/<image-id>.<suffix>`, stores that managed path in metadata, and that `upload_archive` is not a coroutine function.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run python -m pytest tests/test_hybrid.py tests/test_routes.py -q`

Expected: managed-path and synchronous-route assertions fail.

- [ ] **Step 3: Implement minimal fixes**

Copy source images with `shutil.copy2` into the managed image directory before embedding and persistence. Change `async def upload_archive` to `def upload_archive` so FastAPI executes blocking ingestion in its worker threadpool.

- [ ] **Step 4: Run tests and verify GREEN**

Repeat the focused test command; expected: pass.

### Task 4: Share Retrieval Candidates Across Compare Modes

**Files:**
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/store.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/tests/test_hybrid.py`

**Interfaces:**
- Produces: one query embedding and one vector/sparse/full-text/metadata candidate retrieval per `compare_modes` call; each mode still returns a `SearchTrace` with its own weights and fused ranking.

- [ ] **Step 1: Write a failing call-count test**

Use a recording embedding engine/vector store and assert one embedding call, one vector query, one sparse query, one full-text query, and one auxiliary ID load for all four mode traces.

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run python -m pytest tests/test_hybrid.py -q`

Expected: current implementation reports four calls.

- [ ] **Step 3: Implement shared candidate retrieval**

Extract route retrieval from formatting, call it once in `compare_modes`, and invoke `_format_trace` for `balanced`, `semantic`, `keyword`, and `exact` using the same hit lists.

- [ ] **Step 4: Run tests and verify GREEN**

Repeat the focused test command; expected: pass.

### Task 5: Strengthen Rendered-Project Smoke Proof

**Files:**
- Modify: `.github/workflows/main.yml`
- Modify: `tests/test_github_workflows.py`
- Create: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/tests/test_seekdb_integration.py`
- Modify: `templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/README.md`

**Interfaces:**
- Produces: a rendered frontend production build and a real embedded-seekdb integration test using deterministic local embeddings, while hosted-model live proof remains documented/manual unless CI credentials are present.

- [ ] **Step 1: Write failing workflow and integration assertions**

Require `npm run build` in the hybrid smoke job. Add an integration test that constructs the real `OceanbaseVectorStore`, ingests deterministic image fixtures through `HybridImageStore`, and retrieves them without a network model call.

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run python -m pytest tests/test_github_workflows.py -q`

Run in a rendered project: `uv run python -m pytest tests/test_seekdb_integration.py -q`

Expected: workflow assertion fails before the build step is added; integration test drives real embedded seekdb.

- [ ] **Step 3: Implement the smoke workflow and documentation**

Run frontend installation/build in CI after rendering. Document the distinction between deterministic CI infrastructure proof and credentialed live-model proof.

- [ ] **Step 4: Verify GREEN**

Repeat both tests; expected: pass.

### Task 6: Whole-Branch Verification and PR Update

**Files:**
- Review all files changed since `origin/main`.

- [ ] **Step 1: Run complete focused verification**

Run: `uv run python -m pytest tests/cli_commands/test_agentic_rag_hybrid_template.py tests/cli_commands/test_templates_registry.py tests/cli_commands/test_templates_render.py tests/test_docs_lifecycle.py tests/test_github_workflows.py -q`

Run: `make lint typecheck`

Run: `make docs-test`

Render the template, run generated Python tests, install frontend dependencies, run `npm run build`, and run `agentseek doctor` with only `AGENTSEEK_API_KEY` supplied.

- [ ] **Step 2: Request whole-branch code review**

Review `origin/main..HEAD`; fix all Critical and Important findings and re-run their covering tests.

- [ ] **Step 3: Commit and push**

Commit the reviewed repairs and push `codex/agentic-rag-hybrid-template`.

- [ ] **Step 4: Verify hosted PR state**

Confirm PR #123 points to the pushed SHA, is mergeable, and all required checks pass.
