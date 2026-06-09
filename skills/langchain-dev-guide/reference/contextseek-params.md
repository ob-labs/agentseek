# ContextSeek Middleware — Parameter Configuration Issues

This file covers specific parameter-level problems that arise **after** you have decided to use `ContextSeekMiddleware`. For the business scenarios that motivate each parameter group, see [contextseek-middleware.md](contextseek-middleware.md).

---

## Issue 1: scope isolation strategy — fixed at construction vs dynamic per session

**Keywords**: scope isolation, multi-user, thread_id, context bleeding, user isolation, ContextVar, per-session bucket

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
  - **Fallback when before_agent didn't run** (sync invocation without a checkpointer):
    ```python
    # _current_scope() returns _SCOPE_VAR.get() or "default"
    middleware = ContextSeekMiddleware(model=model, embedder=embedder)
    ```
  - **Anti-pattern to avoid** — sharing a fixed-scope instance across users:
    ```python
    # WRONG: all users pollute each other's context
    shared = ContextSeekMiddleware(model=model, embedder=embedder, scope="global")
    agent_for_user_a = create_agent(..., middleware=[shared])
    agent_for_user_b = create_agent(..., middleware=[shared])  # reads user_a's context
    ```
- **Lessons learned**: `scope=` is a deliberate opt-in to shared context. Omitting it is the safe default for multi-user services: `before_agent` populates the ContextVar from `thread_id`, and each asyncio task gets its own isolated copy. The instance itself is never mutated — it is safe to share across agents.

---

## Issue 2: auto_store and record_tool_calls — write volume and side effects

**Keywords**: auto_store, record_tool_calls, write volume, LLM cost spike, storage overhead, intermediate messages skipped, tool provenance

- **Symptom**: After setting `record_tool_calls=True`, storage write volume spikes dramatically, LLM costs for the internal Summarizer shoot up, and agent turn latency increases. Or conversely: `auto_store=True` is the default, but some intermediate AI messages (with `tool_calls`) are unexpectedly NOT being stored.
- **Cause**: The two write paths have very different trigger frequencies:
  - `auto_store` writes in `after_model`, which fires **once per model call** — but only for final answers. The middleware deliberately skips persistence when the `AIMessage` carries `tool_calls` (i.e. an intermediate planning step) to avoid noise. Only a clean text reply (no pending tool calls) is stored.
  - `record_tool_calls` writes in `wrap_tool_call`, which fires **once per individual tool invocation**. A single agent turn that calls 5 tools generates 5 separate `ctx.add()` calls, each triggering the full pipeline: Summarizer (L0 abstract + L1 overview) + embedding + DB write. At scale this multiplies costs by the average number of tool calls per turn.
- **Solution**:
  - **Default configuration** (recommended for most use cases):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=True,          # only final Q+A pairs — low volume
        record_tool_calls=False,  # default; no per-tool writes
    )
    ```
  - **When you need per-tool provenance** (debugging, audit logs, tracing tool decision chains):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=True,
        record_tool_calls=True,   # each tool call stored with tool name, args, result, rationale, task
    )
    ```
    Each stored tool record contains:
    - `tool`: tool name
    - `args`: tool call arguments (after `tool_arg_overrides` are applied)
    - `result`: the ToolMessage content
    - `rationale`: the AIMessage text that preceded the tool call (the model's reasoning)
    - `task`: the last user message
  - **Disable all writes** (retrieval-only mode, e.g. reading from a pre-populated knowledge base):
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_store=False,
        record_tool_calls=False,
    )
    ```
  - **Why intermediate AI messages are skipped**: when the model emits `tool_calls`, the conversation is not done — the assistant has not produced a final answer yet. Storing this half-baked state would degrade retrieval quality because the context would contain questions without coherent answers. The middleware waits for the clean final turn.
- **Lessons learned**: `record_tool_calls=True` is a diagnostic / provenance feature, not a general-purpose setting. Turn it on only for specific debugging sessions or audit pipelines. For production, `auto_store=True` alone builds a useful semantic memory over time with minimal overhead.

---

## Issue 3: auto_compact throttling mechanism and graceful shutdown

**Keywords**: auto_compact, compact_every, graceful shutdown, FastAPI lifespan, RuntimeError, ThreadPoolExecutor, compact frequency

- **Symptom**: You enabled `auto_compact=True` expecting the store to evolve automatically, but compact never seems to run (or runs too rarely). Or, after a FastAPI service restart, you see `RuntimeError: cannot schedule new futures after shutdown` in logs related to ContextSeek.
- **Cause**:
  - `auto_compact` triggers inside `after_agent`, which runs **after the full agent turn**. The trigger condition is: the internal counter for the current scope must reach `compact_every`. So if `compact_every=20` and the agent handles 5 sessions per day, compact fires once every 4 days per scope — much less frequently than expected.
  - The compact task is submitted to a single-threaded `ThreadPoolExecutor` (one worker). A per-scope `threading.Lock` prevents concurrent compaction of the same scope. If a previous compact is still running when the next threshold is crossed, the new trigger is silently dropped (`lock.acquire(blocking=False)`).
  - The executor shuts down via `weakref.finalize` when the middleware instance is garbage collected. If the instance is held as a long-lived object and the application has its own shutdown hook, the finalize may race with framework teardown — producing the `RuntimeError`.
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
    A value of 20–50 balances evolution quality (compact needs enough new material) against freshness (too high means the store rarely evolves).
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
  - **Checking if compact is running**: there is no built-in status probe. Use `LANGSMITH_TRACING=true` to see `ContextSeek.compact` spans in LangSmith, or instrument `_traced_compact` externally.
  - **Manually triggering compact** (outside the middleware loop):
    ```python
    middleware.ctx.compact(scope="my_project")
    ```
- **Lessons learned**: `auto_compact` is a "fire-and-forget evolution" feature — it intentionally drops triggers when the executor is busy to avoid pile-up. It is not a guarantee that compact runs exactly every N turns; only **at most** every N turns and **never** concurrently for the same scope. For critical evolution jobs, prefer explicit scheduled compact calls outside the agent loop.

---

## Issue 4: retrieval_tags and min_score — filtering noisy context injections

**Keywords**: retrieval_tags, min_score, irrelevant context, noisy retrieval, tag filter, score threshold, context pollution, [Relevant Context] noise

- **Symptom**: The `[Relevant Context]` block injected into the system message contains obviously unrelated items that confuse the model. Or a scope holds entries from multiple projects and retrieval cross-contaminates them. Or low-confidence dream-generated hypotheses pollute the context with speculative content the model treats as fact.
- **Cause**: `wrap_model_call` calls `ctx.retrieve(query, scope, k=retrieval_k)` with no tag or score filter by default. Everything in scope that ranks in the top-k is injected, regardless of confidence or provenance tags.
- **Solution**:
  - **Tag-based filtering** — only retrieve items tagged for a specific project or source:
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        retrieval_tags=["project:alpha"],  # AND filter — all tags must be present
    )
    ```
    Tags must be applied when writing items. If using `auto_store`, the middleware writes items without custom tags. Tag filtering is most useful when items were written via `ctx.add(..., tags=[...])` or `plug()` with explicit tags.
  - **Score threshold** — exclude low-confidence / low-relevance items:
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        min_score=0.6,  # only inject items with retrieval score >= 0.6
    )
    ```
  - **Combine both** — tag filter AND score threshold:
    ```python
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        retrieval_tags=["project:alpha"],
        min_score=0.55,
    )
    ```
  - **Exclude dream-generated speculative content** from injection:
    ```python
    # Items tagged "dreamed" have lower confidence and may not be suitable for direct injection.
    # Use min_score to exclude low-confidence dream items, or write dream items to a
    # separate scope and keep the agent's scope clean.
    ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        scope="agent/production",  # dream items written to "agent/research" stay separate
        min_score=0.5,
    )
    ```
- **Lessons learned**: `retrieval_tags` is an AND filter — all listed tags must match. Use it to partition a shared scope (e.g. one scope per tenant, tagged by project). `min_score` is a post-retrieval cutoff applied before injection; the k-nearest neighbors are retrieved first, then filtered. Setting `min_score` too high starves the context block entirely; start around 0.4–0.6 and tune empirically.

---

## Issue 5: tool_arg_overrides — injecting arguments without modifying tool definitions

**Keywords**: tool_arg_overrides, inject arguments, tenant_id, api_key injection, runtime override, model-controlled args, silent replacement

- **Symptom**: A tool (from a library, MCP, or shared codebase) needs a runtime argument like `user_id`, `tenant_id`, or `api_key` injected at call time. You cannot modify the tool's definition, and you don't want the model to be responsible for supplying these values.
- **Cause**: By default, `wrap_tool_call` passes the tool request through unchanged. `tool_arg_overrides` is a constructor-time dict mapping tool names to fixed key-value pairs. Before the tool executes, the middleware merges these overrides into `tool_call["args"]` — the model's arguments are kept, but any key in `overrides` is forcibly replaced. This happens regardless of `record_tool_calls`.
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
  - **Merge semantics**: overrides use `{**tool_args, **overrides}` — the model's supplied values are the base, and the override dict is merged on top. Any key the model passes that is also in `overrides` is silently replaced. The model cannot override the override.
  - **Interaction with record_tool_calls**: when `record_tool_calls=True`, the recorded `args` field reflects the **merged** args (after overrides), so stored provenance is accurate.
  - **Limitation**: overrides are static at construction time. If the injected value must change per session (e.g. a per-request `user_id`), use a custom `wrap_tool_call` middleware instead or pass the value through agent state.
- **Lessons learned**: `tool_arg_overrides` is best for environment-level constants (API keys, tenant IDs, backend names) that should never be model-controlled. Keep the dict small and document it — it is easy to forget that the model's arg is being silently replaced.

---

## Issue 6: dream trigger conditions not met — dream produces zero results

**Keywords**: dream not running, min_items_for_dream, cooldown_hours, DreamStrategy, DREAM_LLM_ENABLED, dream conditions, DreamReport empty, consolidations empty

- **Symptom**: Calling `ctx.dream(scope=...)` returns a `DreamReport` with `consolidation.items=[]` and `divergence=None`. Or the contextseek daemon's lifecycle policy shows no dream activity in logs for days.
- **Cause**: Two pre-conditions must be met before dream produces results:
  1. **Minimum item count** — scope must have ≥ `min_items_for_dream` active items (default **10**). A fresh scope with only a handful of entries produces nothing.
  2. **Divergence requires ≥ 2 tag-based clusters** — the divergence phase groups items by tag and requires at least 2 groups (each with ≥ 2 items). A scope where all items share the same tags produces consolidations only, never divergences. Clusters are built from item tags, not from a retrieval orchestrator.

  Note: `cooldown_hours` (default 6 h) is tracked on the `DreamEngine` instance. Since `ctx.dream()` creates a new engine on every call, the cooldown **does not apply** when calling `ctx.dream()` directly — it only prevents rapid re-triggering inside the daemon lifecycle scheduler.

  Additionally, without `DREAM_LLM_ENABLED=true` the engine uses keyword-overlap heuristics — results are coarser and the similarity window `(0.35, 0.72)` may produce fewer matches.
- **Solution**:
  - **Check scope item count before calling dream**:
    ```python
    report = ctx.overview(scope="my_scope")
    print(report.stage_distribution)  # shows per-stage item counts
    # If total is < 10, add more content before expecting consolidations
    ```
  - **Use dry_run to verify what would be produced**:
    ```python
    report = ctx.dream(scope="my_scope", dry_run=True)
    # dry_run=True runs the full analysis but does not write any items
    consolidation_count = len(report.consolidation.items)
    divergence_count = len(report.divergence.items) if report.divergence else 0
    print(f"Would produce: {consolidation_count} consolidations, {divergence_count} divergences")
    ```
  - **Reduce thresholds in development** (do not use in production):

    `ContextSeekSettings` only exposes `DreamSettings(llm_enabled=bool)`. To override other `DreamStrategy` fields, build the `ContextSeek` instance manually with a custom `StrategyConfig`:
    ```python
    from dataclasses import replace
    from contextseek import ContextSeek, ContextSeekSettings
    from contextseek.config.strategies import DreamStrategy, StrategyConfig

    base_ctx = ContextSeek.from_settings(ContextSeekSettings())
    ctx = replace(
        base_ctx,
        strategy=replace(
            base_ctx.strategy,
            dream=DreamStrategy(
                min_items_for_dream=3,    # default: 10
                divergence_min_clusters=2, # minimum: always 2 (tag-cluster requirement)
            ),
        ),
    )
    ```
  - **Enable LLM for richer synthesis**:
    ```bash
    DREAM_LLM_ENABLED=true
    AGENTSEEK_CTX_LLM_PROVIDER=openai
    AGENTSEEK_CTX_LLM_MODEL=gpt-4o-mini
    ```
    Or in code: `ContextSeekSettings(dream=DreamSettings(llm_enabled=True))`
- **Lessons learned**: Dream is designed for mature scopes with diverse, multi-topic content. Don't expect it to produce useful output from a handful of items on a single topic. In production, call `ctx.dream()` explicitly after bulk ingestion sessions or at fixed intervals (e.g. weekly) — not after every agent turn.

---

## Issue 7: dream-generated items disappear — transient stability and feedback loop

**Keywords**: dream confidence, stability transient, feedback, use it or lose it, dream divergence, relevance_boost, dream item decay, dreamed tag

- **Symptom**: `ctx.dream()` produced a valuable cross-topic hypothesis and the model used it successfully in a few sessions. A week later, the same query no longer returns the hypothesis — it has vanished from the store.
- **Cause**: All dream-generated items (both consolidation and divergence) are written with `stability=transient`. Transient items have a high decay weight in the lifecycle policy — they lose `relevance_boost` quickly and eventually drop below the retrieval score floor. Without positive feedback, dream items are designed to fade: they are hypotheses that need human or model confirmation to earn permanence.

  Divergence items are additionally written with lower initial confidence (default `dream_initial_confidence=0.35` × `0.85` multiplier = ~0.30), making them especially vulnerable to decay.
- **Solution**:
  - **Promote valuable dream items with feedback**:
    ```python
    # After a dream run, review the generated items
    scope = "research/immunology"
    hits = ctx.retrieve("immune regulation", scope=scope, k=20)
    for hit in hits.items:
        # Tags are on hit.item, not on hit directly
        if "dreamed" in (hit.item.tags or []) and human_or_model_approves(hit.item):
            # feedback() requires a full URI ref, not a bare item id
            ref = ctx.resolver.ref_for(scope, hit.item.id)
            ctx.feedback(ref, scope=scope, score=1.0, reason="confirmed cross-domain insight")
    # Positive feedback raises relevance_boost, promoting the item toward stable retention
    ```
  - **Programmatic promotion after model use**: if the model cites a dream item in its answer, treat that as implicit positive feedback:
    ```python
    # Build the ref from scope + item id, then call feedback()
    ref = ctx.resolver.ref_for(scope, dreamed_item_id)
    ctx.feedback(ref, scope=scope, score=0.8, reason="used in model response")
    ```
  - **Inspect dreamed items before they decay** — `overview()` returns stage distribution counts; filter dreamed items by tag separately:
    ```python
    all_items = ctx.items(scope="research/immunology")
    dreamed = [item for item in all_items if "dreamed" in (item.tags or [])]
    print(f"{len(dreamed)} dreamed items pending review")
    ```
  - **Adjust initial confidence for dream items** (if you trust the LLM synthesis):
    ```python
    from dataclasses import replace
    from contextseek.config.strategies import DreamStrategy

    ctx = replace(
        ctx,
        strategy=replace(
            ctx.strategy,
            dream=replace(
                ctx.strategy.dream,
                dream_initial_confidence=0.6,  # default: 0.35 — higher = slower decay
            ),
        ),
    )
    ```
- **Lessons learned**: "Use it or lose it" is intentional — unvalidated hypotheses should not accumulate indefinitely. Build a lightweight review step into your research workflow: after each dream run, iterate over `dreamed` items via `ctx.items()`, apply feedback for the useful ones, and let the rest decay naturally.

---

## Issue 8: evidence_chain vs chain_confidence — which API to use

**Keywords**: evidence_chain, chain_confidence, DAG, overall_confidence, critical_path, conflicts, ConflictReport, performance, provenance API choice

- **Symptom**: You only need to know whether a recommendation is trustworthy enough to act on, but `evidence_chain()` returns a large DAG object that's expensive to process. Or `chain_confidence()` returns a float you can't interpret, with no context about why the confidence is low.
- **Cause**: Both methods traverse the same link graph (`derived_from`, `supported_by`, `merged_from`, `refuted_by`). The difference is output granularity:
  - `chain_confidence(ref, scope)` → `float` — propagated confidence only, no graph construction. Fast.
  - `evidence_chain(ref, scope, max_depth=10)` → `EvidenceChain` — full DAG with `nodes` (`list[ChainNode]`), `edges` (`list[ChainEdge]`), `overall_confidence`, `critical_path` (`list[str]` of item ids), `conflicts` (`list[ConflictReport]`), `broken_links`, and `needs_reverification` (a `bool`).

  Both methods require a **full URI ref**, not a bare item id. Build the ref with `ctx.resolver.ref_for(scope, item_id)`.
- **Solution**:
  - **Use `chain_confidence` for automated gating** (e.g. deciding whether to act on a recommendation):
    ```python
    scope = "incidents/2026-06-01"
    ref = ctx.resolver.ref_for(scope, recommendation_id)
    score = ctx.chain_confidence(ref, scope=scope)
    if score < 0.4:
        flag_for_human_review(recommendation_id)
    else:
        apply_recommendation(recommendation_id)
    ```
  - **Use `evidence_chain` when you need to explain or visualize the reasoning**:
    ```python
    scope = "incidents/2026-06-01"
    ref = ctx.resolver.ref_for(scope, recommendation_id)
    chain = ctx.evidence_chain(ref, scope=scope, max_depth=10)

    print(f"Confidence: {chain.overall_confidence:.2f}")

    # critical_path is a list[str] of item ids — expand to get content
    path_items = ctx.expand_by_ids(chain.critical_path, scope=scope)
    print(f"Critical path: {[item.content[:60] for item in path_items]}")

    if chain.conflicts:
        # conflicts is list[ConflictReport]; each has item_id, refuter_id, refutation_strength
        print("Conflicting evidence detected:")
        for c in chain.conflicts:
            print(f"  - item={c.item_id} refuted_by={c.refuter_id} strength={c.refutation_strength:.2f}")

    if chain.broken_links:
        print(f"Broken references: {len(chain.broken_links)} items no longer exist")

    if chain.needs_reverification:
        print("Overall confidence below threshold — flag for re-investigation")
    ```
  - **Reverification threshold**: `chain.needs_reverification` is a `bool` — it is `True` when `overall_confidence` falls below `0.4` (the built-in `reverification_threshold`). Use it as a signal to queue the item for human review before acting on it.
  - **When no links exist**: if items were written without `links=`, both methods return the item's own `confidence` field unchanged — there is no graph to traverse. Write `links=` on `ctx.add()` calls to enable meaningful provenance.
- **Lessons learned**: `chain_confidence` is the right call for high-frequency automated checks (e.g. every retrieved item). `evidence_chain` is for postmortem analysis, audit reports, or dashboards where you need to present the reasoning chain to a human. Avoid calling `evidence_chain` in the hot path of every agent turn.

---

## Issue 9: DataPlug vs manual ctx.add() — choosing the right bulk import path

**Keywords**: DataPlug, plug, bulk import, RAGPlug, PowerMemPlug, batch add, streaming ingest, ctx.add loop, which to use

- **Symptom**: You need to write 10,000 records to contextseek before deploying an agent. You're unsure whether to loop `ctx.add()` or use `ctx.plug()` with a `DataPlug`, and whether the two differ in how scope, stage, and metadata are handled.
- **Cause**: Both paths ultimately call the same internal pipeline (summarizer → embedder → conflict check → persist). The difference is at the **input interface** and **metadata forwarding**:
  - `ctx.add(content, *, scope, source, ...)` — one item, caller controls all parameters explicitly. Best for custom pipelines where you preprocess each record.
  - `ctx.plug(plug, *, scope)` — consumes a streaming `DataPlug`; each `RawEvent` can carry `metadata` that overrides `scope`, `stage`, `stability`, `embedding`, `importance`, and `summary` inline. Best for adapting existing data sources.
- **Solution**:
  - **Use `plug()` when adapting an existing source** (RAG, PowerMem, traces):
    ```python
    from contextseek.plugs import RAGPlug

    plug = RAGPlug(source=vector_store.as_iterable(), source_id="wiki-v2")
    ctx.plug(plug, scope="company/knowledge")
    # RAGPlug yields RawEvents; metadata can carry per-item scope/stage overrides
    ```
  - **Use `ctx.add()` in a loop for custom preprocessing**:
    ```python
    for record in my_data_source:
        processed = preprocess(record)
        ctx.add(
            processed.text,
            scope="company/knowledge",
            source=record.source_id,
            tags=record.project_tags,
            stage="raw",
        )
    ```
  - **Override stage per event with plug()** (e.g. import pre-summarized items directly as `extracted`):
    ```python
    from contextseek.protocols.plugs import RawEvent

    events = [
        RawEvent(
            content=item.text,
            source=item.source_id,
            metadata={"stage": "extracted", "summary": item.existing_summary},
        )
        for item in pre_summarized_items
    ]
    # Wrap as a simple DataPlug
    class ListPlug:
        def stream(self): return iter(events)
        def metadata(self): return PlugMeta(name="pre-summarized", source_type="knowledge")

    ctx.plug(ListPlug(), scope="company/knowledge")
    ```
- **Lessons learned**: `plug()` is the idiomatic path for integrating existing external sources. It handles the `PlugMeta → SourceType` mapping and per-event metadata merging out of the box. Manual `ctx.add()` loops are appropriate when you have non-standard preprocessing logic, need precise control over each item's provenance fields, or are writing fewer than a few hundred items.

---

## Issue 10: plug() scope priority and stage inference behavior

**Keywords**: plug scope priority, event metadata scope, DataPlug name, stage override, RAG stage, TracePlug, scope assignment, unexpected scope

- **Symptom**: After calling `ctx.plug(rag_plug, scope="project:x")`, some items end up in a different scope. Or items from a `TracePlug` import end up with `stage=raw` when you expected `stage=extracted`.
- **Cause**:
  - **Scope resolution priority**: `plug(scope=...)` parameter → `event.metadata["scope"]` → `plug.metadata().name`. Passing `scope=` in the `plug()` call forces **all** events to that scope, regardless of what individual events declare. If you omit `scope=` from `plug()`, each event can control its own scope via `metadata`.
  - **Stage inference**: if neither `event.metadata["stage"]` nor a plug-level default is set, `plug()` falls back to `stage="raw"` for all items. `TracePlug` and skill importers set their own default stages (`trace_extraction` → `raw`; `MCPToolImporter` → `skill`), but `RAGPlug` defaults to `raw` unless the source metadata carries a `stage` key.
- **Solution**:
  - **Force all events to one scope** (recommended for most bulk imports):
    ```python
    ctx.plug(rag_plug, scope="company/knowledge")
    # All events land in "company/knowledge" regardless of event.metadata["scope"]
    ```
  - **Allow per-event scope** (when source data has meaningful sub-scopes):
    ```python
    # Omit scope= in plug(); events control their own scope via metadata
    ctx.plug(rag_plug)
    # Each RawEvent.metadata["scope"] = "dept/engineering" or "dept/hr" etc.
    ```
  - **Set stage at the event level** to skip redundant summarization for pre-processed content:
    ```python
    RawEvent(
        content=chunk.text,
        source="wiki",
        metadata={"stage": "extracted", "summary": chunk.summary, "scope": "company/knowledge"},
    )
    ```
  - **Verify what landed after a plug run**:
    ```python
    items = ctx.items(scope="company/knowledge")
    stage_counts = Counter(item.stage.value for item in items)
    print(stage_counts)  # e.g. {"raw": 9500, "extracted": 500}
    ```
- **Lessons learned**: when in doubt, always pass `scope=` explicitly to `plug()` — it is the simplest way to ensure all imported items end up in the right bucket. Per-event scope override is a power-user feature for heterogeneous source data where different records naturally belong in different scopes.

---

## Issue 11: auto_dream — automatic dream triggering inside the agent loop

**Keywords**: auto_dream, dream_every, dream_min_interval_seconds, middleware dream, automatic dream, dual gate, fire-and-forget dream

- **Symptom**: You want the agent's knowledge store to automatically discover cross-topic patterns without calling `ctx.dream()` explicitly after every session. Or you enabled `auto_dream=True` but dream never seems to fire, even after many sessions.
- **Cause**: `ContextSeekMiddleware` supports an optional automatic dream trigger alongside `auto_compact`. It uses a **dual gate** to avoid over-triggering: both conditions must be satisfied before dream fires:
  1. **Turn counter gate** — the scope's internal counter must reach `dream_every` (default **200**). So if `dream_every=200` and the agent handles 10 sessions per day, dream fires once every 20 days per scope — much less frequently than compact.
  2. **Time gate** — at least `dream_min_interval_seconds` must have elapsed since the last dream triggered by this middleware instance (default **3600 s = 1 h**). This prevents back-to-back firing even if the counter is satisfied repeatedly.

  Both gates must pass in the same `after_agent` call. The dream task is submitted fire-and-forget (same `ThreadPoolExecutor` as compact) — it does **not** block the agent response.

  Note: this is separate from the cooldown in `DreamStrategy.cooldown_hours`, which is tracked on the `DreamEngine` instance and does not apply when `ContextSeek.dream()` is called directly. The middleware's `dream_min_interval_seconds` is tracked on the middleware instance.
- **Solution**:
  - **Enable automatic dream with sensible defaults**:
    ```python
    middleware = ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_compact=True,
        compact_every=20,
        auto_dream=True,
        dream_every=200,               # fire after every 200 agent turns per scope
        dream_min_interval_seconds=3600.0,  # and at least 1 hour since last dream
    )
    ```
  - **For high-traffic services** (many turns per day) — lower the turn threshold:
    ```python
    middleware = ContextSeekMiddleware(
        model=model,
        embedder=embedder,
        auto_dream=True,
        dream_every=50,                # fire more frequently
        dream_min_interval_seconds=7200.0,  # but no more than once every 2 hours
    )
    ```
  - **Graceful shutdown** — `middleware.shutdown(wait=True)` waits for both in-flight compact **and** dream tasks:
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        middleware.shutdown(wait=True)
    ```
  - **Check if dream has fired** — there is no built-in status probe. Use `LANGSMITH_TRACING=true` to see `ContextSeek.dream` spans, or inspect `ctx.items(scope=..., stage=Stage.extracted)` for items tagged `dreamed`.
  - **Manually trigger dream outside the middleware loop** (recommended for research / bulk-import workflows):
    ```python
    # Bypass both gates; always runs immediately
    report = middleware.ctx.dream(scope="my_scope")
    print(f"New items: {report.total_dream_items}")
    ```
- **Lessons learned**: `auto_dream` is designed for long-running conversational agents that accumulate hundreds of sessions. For lower-volume or batch scenarios (e.g. a research agent that ingests documents in bursts), explicit `ctx.dream()` calls after each ingestion batch give more control over timing and cost. `auto_dream=True` and explicit `ctx.dream()` calls can coexist — they use the same underlying `DreamEngine`.
