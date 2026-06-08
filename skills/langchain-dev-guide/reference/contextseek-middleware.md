# ContextSeek Middleware Development Issues

## Issue 1: Agent loses context across sessions — adding semantic memory beyond the filesystem

- **Symptom**: Your agent starts fresh every conversation. It can't recall user preferences, past decisions, or prior task outcomes. The filesystem-based `memory=` approach (via `StoreBackend`) works for explicit notes the agent writes, but doesn't help with implicit knowledge buried in past conversations. You need the agent to automatically draw on semantically relevant history without the agent having to manage files.
- **Cause**: The default LangChain agent loop has no persistent memory. The `StoreBackend` + `memory=` pattern (from Deep Agents) gives the agent a writable file it can read and update, but the agent itself must decide what to write — it degrades when conversation history is long or unstructured. What's missing is a retrieval layer that automatically surfaces relevant past context before each model call, without the agent being involved.
- **Solution**: Add `ContextSeekMiddleware` to the agent's `middleware=` list. It passively sidecars the agent loop: before every model call it retrieves semantically relevant items from a vector store and injects them into the system message; after every final answer it stores the Q+A pair for future retrieval. The agent has no awareness of any of this.
  - **Install** (choose one):
    ```bash
    # Inside the agentseek project
    pip install "agentseek[context]"

    # Standalone
    pip install contextseek contextseek-bridges-langchain
    ```
  - **Configure via env vars** (copy from `.env.example`, section "ContextSeek semantic context layer"). All constructor parameters are optional — the middleware reads configuration from env vars when none are passed:
    ```bash
    # Storage backend (default: memory — ephemeral, no persistence).
    # Use seekdb for local persistent storage with built-in ONNX embedder
    # (all-MiniLM-L6-v2, no external API key required):
    AGENTSEEK_CTX_STORAGE_BACKEND=seekdb

    # Optional: LLM for richer L0/L1 abstracts. Without it, raw Q&A text is stored
    # (still fully retrievable via seekdb's built-in vector search).
    AGENTSEEK_CTX_LLM_PROVIDER=openai
    AGENTSEEK_CTX_LLM_MODEL=gpt-4o-mini
    ```
    The `AGENTSEEK_CTX_*` prefix is automatically aliased to the env vars contextseek reads internally — no credential duplication needed.
  - **Minimum integration** (zero constructor arguments):
    ```python
    from langchain.agents import create_agent
    from contextseek.bridges.langchain.middleware import ContextSeekMiddleware

    agent = create_agent(
        model=model,
        tools=[...],
        middleware=[ContextSeekMiddleware()],
    )
    ```
  - **Passing the agent's own model and embedder** (avoids a second model instantiation):
    ```python
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    model = ChatOpenAI(model="gpt-4o")
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    agent = create_agent(
        model=model,
        tools=[...],
        middleware=[ContextSeekMiddleware(model=model, embedder=embedder)],
    )
    ```
  - **What happens at runtime** (fully transparent to the agent):
    1. Before each model call: retrieves the top-k semantically relevant items from the store and appends them to the system message as a `[Relevant Context]` block
    2. After each final answer: stores the Q+A pair for future retrieval
- **Lessons learned**: `ContextSeekMiddleware` and the filesystem `memory=` approach solve different problems and can coexist. Use `memory=` when the agent needs to explicitly read and write structured notes. Use `ContextSeekMiddleware` when you want the agent's accumulated conversation history to automatically inform future answers — no agent-side file management required.

## Issue 2: scope isolation strategy — fixed at construction vs dynamic per session

- **Symptom**: In a multi-user service, different users' context bleeds into each other — one user sees context retrieved from another user's conversation history. Or a single-user bot uses `thread_id` as scope but the context appears to reset on each invocation.
- **Cause**: A `ContextSeekMiddleware` instance is shared across all concurrent agent sessions (it is stateless except for the compact executor). Scope determines which "bucket" in the store is read and written. There are two distinct resolution paths:
  - **Constructor `scope=` is given**: this value is hard-wired for every session this instance handles — `_SCOPE_VAR` (the per-task ContextVar) is **not** consulted. All sessions share the same bucket regardless of `thread_id`.
  - **Constructor `scope=` is omitted (or `None`)**: `before_agent` runs at the start of each agent turn and sets `_SCOPE_VAR` to `runtime.thread_id` for the current asyncio task. Every downstream hook (`wrap_model_call`, `after_model`, `wrap_tool_call`) reads the ContextVar, so concurrent sessions are naturally isolated without touching the instance.
- **Solution**:
  - **Single-tenant / shared knowledge base** (all sessions read and write the same context):
    ```python
    # Every session contributes to and retrieves from "my_project"
    middleware = ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        scope="my_project",
    )
    ```
  - **Multi-user isolation** (each session gets its own isolated context bucket):
    ```python
    # Do NOT pass scope= — let before_agent pick up runtime.thread_id
    middleware = ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        # scope= omitted
    )

    # Callers must pass a stable, user-specific thread_id in config
    agent.invoke(
        {"messages": [...]},
        config={"configurable": {"thread_id": f"user:{user_id}"}},
    )
    ```
  - **Per-conversation isolation with a fallback** (scope set externally but with a default):
    ```python
    # The middleware falls back to "default" when before_agent didn't run
    # (e.g. sync invocation without a checkpointer). This is the built-in behavior.
    middleware = ContextSeekMiddleware(model=model, embedder=embedder)
    # _current_scope() returns _SCOPE_VAR.get() or "default"
    ```
  - **Anti-pattern to avoid** — sharing a fixed-scope instance across users:
    ```python
    # WRONG: all users pollute each other's context
    shared = ContextSeekMiddleware(model=model, embedder=embedder, scope="global")
    agent_for_user_a = create_agent(..., middleware=[shared])
    agent_for_user_b = create_agent(..., middleware=[shared])  # reads user_a's context
    ```
- **Lessons learned**: The `scope=` parameter is a deliberate opt-in to shared context. Omitting it is the safe default for multi-user services: `before_agent` will populate the ContextVar from `thread_id`, and each asyncio task gets its own isolated copy of the variable. The instance itself is never mutated — it is safe to share.

## Issue 3: auto_store and record_tool_calls write volume and side effects

- **Symptom**: After setting `record_tool_calls=True`, storage write volume spikes dramatically, LLM costs for the internal Summarizer shoot up, and agent turn latency increases. Or conversely: `auto_store=True` is the default, but some intermediate AI messages (with tool_calls) are unexpectedly NOT being stored.
- **Cause**: The two write paths have very different trigger frequencies:
  - `auto_store` writes in `after_model`, which fires **once per model call** — but only for final answers. The middleware deliberately skips persistence when the `AIMessage` carries `tool_calls` (i.e. an intermediate planning step) to avoid noise. Only a clean text reply (no pending tool calls) is stored.
  - `record_tool_calls` writes in `wrap_tool_call`, which fires **once per individual tool invocation**. A single agent turn that calls 5 tools generates 5 separate `ctx.add()` calls, each triggering the full pipeline: Summarizer (L0 abstract + L1 overview) + embedding + DB write. At scale this multiplies costs by the average number of tool calls per turn.
- **Solution**:
  - **Default configuration** (recommended for most use cases):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=True,       # only final Q+A pairs — low volume
        record_tool_calls=False,  # default; no per-tool writes
    )
    ```
  - **When you need per-tool provenance** (debugging, audit logs, tracing tool decision chains):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=True,
        record_tool_calls=True,  # each tool call stored with tool name, args, result, rationale, task
    )
    ```
    Each stored tool record contains:
    - `tool`: tool name
    - `args`: tool call arguments
    - `result`: the ToolMessage content
    - `rationale`: the AIMessage text that preceded the tool call (the model's reasoning)
    - `task`: the last user message (what the user originally asked)
  - **Disable all writes** (retrieval-only mode, e.g. read from a pre-populated knowledge base):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=False,
        record_tool_calls=False,
    )
    ```
  - **Why intermediate AI messages are skipped**: when the model emits `tool_calls`, the conversation is not done — the assistant has not produced a final answer yet. Storing this half-baked state would degrade retrieval quality because the context would contain questions without coherent answers. The middleware waits for the clean final turn.
- **Lessons learned**: `record_tool_calls=True` is a diagnostic / provenance feature, not a general-purpose setting. Turn it on only for specific debugging sessions or audit pipelines. For production, `auto_store=True` alone is sufficient to build up a useful semantic memory over time with minimal overhead.

## Issue 4: auto_compact throttling mechanism and graceful shutdown

- **Symptom**: You enabled `auto_compact=True` expecting the store to evolve automatically, but compact never seems to run (or runs too rarely). Or, after a FastAPI service restart, you see `RuntimeError: cannot schedule new futures after shutdown` in the logs related to ContextSeek.
- **Cause**:
  - `auto_compact` triggers inside `after_agent`, which runs **after the full agent turn** (including all tool calls and the final answer). The trigger condition is: the internal counter for the current scope must reach `compact_every`. So if `compact_every=20` and the agent handles 5 sessions a day, compact fires once every 4 days per scope — much less frequently than one might expect.
  - The compact task is submitted to a single-threaded `ThreadPoolExecutor` (one worker). A per-scope `threading.Lock` prevents the same scope from compacting concurrently. If the previous compact for a scope is still running when the next threshold is crossed, the new trigger is silently dropped (non-blocking `lock.acquire(blocking=False)`).
  - The executor is shut down automatically via `weakref.finalize` when the middleware instance is garbage collected. But if the instance is held by the application as a long-lived object and the application has its own shutdown hook, the `weakref.finalize` may race with framework teardown — producing the `RuntimeError`.
- **Solution**:
  - **Recommended compact settings for production**:
    ```python
    middleware = ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_compact=True,
        compact_every=20,  # trigger after every 20 completed agent turns per scope
    )
    ```
    A value of 20–50 balances evolution quality (compact needs enough new material to work with) against freshness (too high means the store never evolves).
  - **Graceful shutdown in FastAPI lifespan**:
    ```python
    from contextlib import asynccontextmanager
    from fastapi import FastAPI

    middleware = ContextSeekMiddleware(model=model, embedder=embedder, auto_compact=True)
    agent = create_agent(model=model, tools=[...], middleware=[middleware])

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        middleware.shutdown(wait=True)  # wait for any in-flight compact to finish

    app = FastAPI(lifespan=lifespan)
    ```
  - **Checking if compact is running**: there is no built-in status probe. Use `LANGSMITH_TRACING=true` to see `ContextSeek.compact` spans in LangSmith, or instrument the `_traced_compact` call externally.
  - **Manually triggering compact** (outside the middleware loop):
    ```python
    middleware.ctx.compact(scope="my_project")
    ```
- **Lessons learned**: `auto_compact` is a "fire-and-forget evolution" feature — it intentionally drops triggers when the executor is busy to avoid pile-up. Design around this: it is not a guarantee that compact runs exactly every N turns, only that it runs **at most** every N turns and **never** concurrently for the same scope. For critical evolution jobs, prefer explicit scheduled compact calls outside the agent loop.

## Issue 5: tool_arg_overrides — injecting arguments without modifying tool definitions

- **Symptom**: A tool (from a library, MCP, or shared codebase) needs a runtime argument like `user_id`, `tenant_id`, or `api_key` injected at call time. You cannot modify the tool's definition, and you don't want the model to be responsible for supplying these values.
- **Cause**: By default, `wrap_tool_call` passes the tool request through unchanged. `tool_arg_overrides` is a constructor-time dict that maps tool names to a set of fixed key-value pairs. Before the tool executes, the middleware merges these overrides into `tool_call["args"]` — the model's arguments are kept, but any key present in `overrides` is forcibly replaced. This happens regardless of `record_tool_calls`.
- **Solution**:
  - **Inject a fixed tenant ID into one tool**:
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        tool_arg_overrides={
            "search_knowledge_base": {"tenant_id": "acme-corp"},
        },
    )
    ```
  - **Override multiple tools**:
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        tool_arg_overrides={
            "send_email":    {"from_address": "bot@company.com"},
            "write_to_db":   {"db_name": "prod", "schema": "agents"},
            "call_external": {"api_key": os.environ["EXTERNAL_API_KEY"]},
        },
    )
    ```
  - **Merge semantics**: overrides use `{**tool_args, **overrides}` — the model's supplied values are the base, and the override dict is merged on top. Any key the model passes that is also in `overrides` will be silently replaced by the override value. The model cannot override the override.
  - **Interaction with record_tool_calls**: when `record_tool_calls=True`, the recorded `args` field reflects the **merged** args (after overrides are applied), so the stored provenance is accurate.
  - **Limitation**: overrides are static at construction time. If the injected value needs to change per session (e.g. `user_id` per request), `tool_arg_overrides` is not the right tool — use a custom `wrap_tool_call` middleware instead, or pass the value through agent state.
- **Lessons learned**: `tool_arg_overrides` is best suited for environment-level constants (API keys, tenant IDs, backend names) that should never be model-controlled. It is a lightweight alternative to wrapping every tool in a closure or adding hidden parameters to tool schemas. Keep the override dict small and document it clearly — it is easy to forget that the model's arg is being silently replaced.
