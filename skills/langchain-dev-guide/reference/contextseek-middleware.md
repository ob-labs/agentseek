# ContextSeek Middleware — Use Case Scenarios

Every scenario below answers one question: **"I'm building X — is ContextSeekMiddleware the right fit, and how do I wire it in?"** Parameter-level configuration issues that arise after the decision to use the middleware are covered in [contextseek-params.md](contextseek-params.md).

---

## Issue 1: Agent loses context across sessions — personal assistant or support bot

**Keywords**: semantic memory, context loss, cross-session, agent forgets, StoreBackend alternative, vector retrieval, passive memory, persistent memory

You're building a **personal coding assistant** or a **customer support bot**. Users notice the agent "forgets" everything between sessions: an architecture decision made last week ("we chose OceanBase over Redis because of HTAP requirements") is unknown to the agent today; a support user who already explained their account type and preferred language has to explain it again on every new conversation.

The instinct is to reach for `memory=` and `StoreBackend` (from Deep Agents). That works — but only for knowledge the agent actively chooses to write down. It degrades when conversation history is long or when the agent doesn't "know" what's worth remembering. What's missing is a passive retrieval layer that automatically surfaces semantically relevant history before each model call without any agent involvement.

`ContextSeekMiddleware` sidecars the agent loop transparently:

1. **Before every model call**: retrieves the top-k semantically relevant items from the vector store and appends them to the system message as a `[Relevant Context]` block.
2. **After every final answer**: stores the Q+A pair for future retrieval (skips intermediate tool-call turns to avoid noise).

The agent is never aware of either step.

- **Install**:
  ```bash
  # Inside the agentseek project
  pip install "agentseek[context]"

  # Standalone
  pip install contextseek contextseek-bridges-langchain
  ```
- **Configure via env vars** (copy from `.env.example`, section "ContextSeek semantic context layer"). All constructor parameters are optional — the middleware reads from env when nothing is passed:
  ```bash
  # seekdb = local persistent storage, built-in ONNX embedder (no API key needed)
  AGENTSEEK_CTX_STORAGE_BACKEND=seekdb

  # Optional LLM for richer L1 summaries
  AGENTSEEK_CTX_LLM_PROVIDER=openai
  AGENTSEEK_CTX_LLM_MODEL=gpt-4o-mini
  ```
  The `AGENTSEEK_CTX_*` prefix is automatically aliased to the env vars contextseek reads internally — no credential duplication.
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
- **Sharing the agent's own model and embedder** (avoids a second model instantiation):
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
- **Lessons learned**: `ContextSeekMiddleware` and `memory=` (StoreBackend) solve different problems and can coexist in the same agent. Use `memory=` when the agent needs to explicitly read and write structured notes it controls. Use `ContextSeekMiddleware` when you want the agent's accumulated conversation history to automatically inform future answers — no agent-side file management required.

**Common configuration problems for this scenario** → see [contextseek-params.md](contextseek-params.md): scope isolation (multi-user context bleeding), auto_compact throttling and graceful shutdown, retrieval_tags / min_score filtering noisy context, tool_arg_overrides for injecting runtime arguments.

---

## Issue 2: Multi-tool data-pipeline agent — auditing tool call decisions

**Keywords**: tool provenance, audit trail, tool call history, data pipeline agent, record_tool_calls, why did agent choose this query, compliance, tool decision tracing

You're building a **data analysis agent** that, on each task, calls a chain of tools: `query_db` → `run_sql` → `transform_data` → `generate_chart` — typically 5–10 tool invocations per turn. A compliance requirement asks: *"Why did the agent choose that particular SQL query? Were the tool arguments reasonable?"* Your team also needs to reproduce past analyses from stored tool traces.

`ContextSeekMiddleware` with `record_tool_calls=True` writes a structured record for each tool invocation into the vector store. Each record captures:

- `tool` — tool name
- `args` — arguments passed (after any `tool_arg_overrides` are applied)
- `result` — the ToolMessage content
- `rationale` — the AIMessage text that preceded the tool call (the model's stated reasoning)
- `task` — the originating user message

These records are retrievable by future agent turns: *"What SQL did we use for the Q3 revenue report last month?"* can return the exact query with its rationale.

- **Integration**:
  ```python
  middleware = ContextSeekMiddleware(
      model=model,
      embedder=embedder,
      auto_store=True,          # store final Q+A pairs
      record_tool_calls=True,   # additionally store each tool invocation
  )
  agent = create_agent(model=model, tools=[query_db, run_sql, transform_data, generate_chart], middleware=[middleware])
  ```
- **Retrieval-only mode** — read historical tool traces without writing new ones (e.g. a read-only audit agent):
  ```python
  ContextSeekMiddleware(
      model=model,
      embedder=embedder,
      auto_store=False,
      record_tool_calls=False,  # retrieval only; no writes
  )
  ```
- **Lessons learned**: `record_tool_calls=True` multiplies write volume by the average number of tool calls per turn. Each call triggers the full summarizer + embedding + DB write pipeline. For a 5-tool agent, that is 5× the LLM cost per turn compared to `auto_store=True` alone. Only enable it when you actually need per-tool provenance.

**Common configuration problems for this scenario** → see [contextseek-params.md](contextseek-params.md): auto_store / record_tool_calls write volume and cost spikes.

---

## Issue 3: Research agent accumulates raw notes — cross-topic pattern discovery

**Keywords**: dream, cross-topic pattern, consolidation, divergence, knowledge synthesis, idle-time, hypothesis generation, dreaming, research agent, implicit connections

You're building a **literature research agent** that writes dozens of raw research summaries per day across multiple topics. After a week the store holds 200+ items but the agent can only retrieve "known" content — it misses implicit cross-topic connections: "gene editing for Alzheimer's treatment" and "mRNA vaccine T-cell activation" both involve immune regulation mechanisms, but no item makes that bridge explicit. You need the system to synthesize new insights from accumulated material without re-running the full agent.

`ctx.dream()` runs offline in two phases:

1. **Consolidation** — scans recently active, un-dreamed items. Within a similarity window `(0.35, 0.72)` — related but not duplicates — it synthesizes new `extracted`-stage items that surface implicit patterns. Tagged `dreamed`, `consolidation`.
2. **Divergence** — generates cross-cluster hypothesis items bridging dissimilar topic clusters. Tagged `dreamed`, `divergence`. Confidence is lower (×0.85 multiplier) — these are hypotheses, not facts.

Dream items have `stability=transient` and decay fast. They are "use it or lose it": `ctx.feedback(ref, score=1.0)` on a valuable hypothesis promotes it to a stable item; otherwise it fades within days.

- **Trigger dream manually after a research session**:
  ```python
  from contextseek import ContextSeek

  ctx = ContextSeek.from_settings()
  report = ctx.dream(scope="research/immunology")
  consolidation_count = len(report.consolidation.items)
  divergence_count = len(report.divergence.items) if report.divergence else 0
  print(f"Consolidations: {consolidation_count}, Divergences: {divergence_count}")
  ```
- **Review and promote valuable dream items**:
  ```python
  scope = "research/immunology"
  # ctx.overview() returns stage distribution counts; dreamed items are filtered by tag separately
  all_items = ctx.items(scope=scope)
  dreamed = [item for item in all_items if "dreamed" in (item.tags or [])]

  for item in dreamed:
      if human_review_approves(item):
          # feedback() requires a full URI ref, not a bare item id
          ref = ctx.resolver.ref_for(scope, item.id)
          ctx.feedback(ref, scope=scope, score=1.0, reason="confirmed cross-domain insight")
  ```
- **Enable LLM-enhanced dream** (richer synthesis):
  ```bash
  DREAM_LLM_ENABLED=true
  # uses the same LLM configured for the agent; no separate key needed
  ```
- **Lessons learned**: By default `ContextSeekMiddleware` does **not** trigger `dream()` — it only handles `compact()`. For research workflows, call `ctx.dream()` explicitly after bulk ingestion sessions, or schedule it via cron / the contextseek daemon lifecycle. If you want automatic dream triggering inside the agent loop, set `auto_dream=True` on the middleware (see [contextseek-params.md](contextseek-params.md) Issue 11 for the dual-gate trigger mechanics). Dream without LLM falls back to keyword-overlap heuristics; results are coarser but still useful for surface-level clustering.

**Common configuration problems for this scenario** → see [contextseek-params.md](contextseek-params.md): dream trigger conditions not met (min_items, cooldown), dream-generated items disappearing due to transient stability.

---

## Issue 4: SRE incident postmortem agent — tracing knowledge confidence and conflicts

**Keywords**: evidence_chain, provenance, confidence propagation, conflict detection, SRE, postmortem, audit, upstream, chain_confidence, broken links, knowledge trustworthiness

You're building an **incident postmortem agent** that accumulates observations during a live incident: "Alert A fired at 14:03", "Log B shows connection timeouts", "Analysis: timeouts caused by DB connection pool exhaustion", "Recommendation: lower `connection_timeout` to 500ms". Each item is derived from the previous. A week later, during a recurring-incident review, an engineer asks: *"Is this recommendation actually well-supported? Were there any conflicting signals? How confident should we be in this diagnosis?"*

`ctx.evidence_chain()` constructs a full DAG starting from any item, traversing `derived_from`, `supported_by`, `merged_from` (positive) and `refuted_by` (negative) links. It returns:

- `overall_confidence` — propagated confidence score (Noisy-OR for supports, penalty for refutations)
- `critical_path` — `list[str]` of item ids forming the highest-weight inference path
- `conflicts` — `list[ConflictReport]`; each has `item_id`, `refuter_id`, `refutation_strength`
- `broken_links` — `list[str]` of item ids that no longer exist in the store
- `nodes` / `edges` — full DAG for visualization
- `needs_reverification` — `bool`; `True` when `overall_confidence < 0.4`

- **Write items with explicit derivation links**:
  ```python
  from contextseek import ContextSeek
  from contextseek.domain.links import Link, LinkType

  ctx = ContextSeek.from_settings()
  scope = "incidents/2026-06-01"

  alert = ctx.add("Alert A fired at 14:03: p99 latency > 2s", scope=scope, source="pagerduty")
  log   = ctx.add("Log B: connection pool exhausted (pool_size=10, wait_timeout=30s)",
                  scope=scope, source="datadog",
                  links=[Link(target_id=alert.id, relation=LinkType.supported_by)])
  analysis = ctx.add("Root cause: DB connection pool exhausted under 50-rps load",
                     scope=scope, source="agent_inference",
                     links=[Link(target_id=log.id, relation=LinkType.derived_from)])
  rec = ctx.add("Recommendation: lower connection_timeout to 500ms",
                scope=scope, source="agent_inference",
                links=[Link(target_id=analysis.id, relation=LinkType.derived_from)])
  ```
- **Evaluate the recommendation's trustworthiness**:
  ```python
  # evidence_chain and chain_confidence require a full URI ref, not a bare item id
  ref = ctx.resolver.ref_for(scope, rec.id)
  chain = ctx.evidence_chain(ref, scope=scope)
  print(f"Confidence: {chain.overall_confidence:.2f}")  # e.g. 0.71
  if chain.conflicts:
      # conflicts is list[ConflictReport]; each has item_id, refuter_id, refutation_strength
      for c in chain.conflicts:
          print(f"Conflicting evidence: {c.refuter_id} refutes {c.item_id} (strength={c.refutation_strength:.2f})")
  if chain.overall_confidence < 0.4:
      print("Low confidence — needs human review before applying")
  ```
- **Quick check without the full DAG**:
  ```python
  ref = ctx.resolver.ref_for(scope, rec.id)
  score = ctx.chain_confidence(ref, scope=scope)
  # returns a float; same traversal as evidence_chain but no DAG construction overhead
  ```
- **Lessons learned**: the agent itself doesn't need to call `evidence_chain` — it's a postmortem / audit API. Wire it into your review pipeline or a separate audit agent that periodically evaluates low-confidence recommendations. Writing `links=` when calling `ctx.add()` is optional but unlocks this entire capability; without links, `evidence_chain` sees only isolated nodes.

**Common configuration problems for this scenario** → see [contextseek-params.md](contextseek-params.md): evidence_chain vs chain_confidence — when to use which.

---

## Issue 5: Enterprise knowledge migration — agent is retrieval-ready on day one

**Keywords**: pre-populate, cold start, bulk import, DataPlug, RAGPlug, PowerMemPlug, existing knowledge, seed context, initial corpus, plug, knowledge migration

You're migrating an enterprise knowledge base to a ContextSeek-backed agent. The existing data is 100 k+ FAQ entries, historical support tickets, and internal wiki pages — currently stored in a RAG vector store or PowerMem. The new agent cannot wait months for `auto_store` to accumulate conversation history; it needs to be able to retrieve from all of this on day one.

`ctx.plug()` consumes a `DataPlug` (a streaming iterator of `RawEvent` objects) and routes each event through the same full pipeline as `ctx.add()`: summarization, embedding, conflict detection, and persistence. Built-in plugs cover the most common sources:

| Plug class | Source |
|------------|--------|
| `RAGPlug` | Existing RAG / vector store chunks |
| `PowerMemPlug` | PowerMem memory store |
| `TracePlug` | Execution traces / agent logs |
| `MCPToolImporter` | MCP tool definitions → `skill` stage |
| `OpenAIFunctionImporter` | OpenAI function schemas → `skill` stage |

- **Import from an existing RAG store**:
  ```python
  from contextseek import ContextSeek
  from contextseek.plugs import RAGPlug

  ctx = ContextSeek.from_settings()

  # RAGPlug accepts a list of dicts; each dict needs at least "content" or "page_content"
  docs = existing_vector_store.similarity_search("*", k=10000)
  rag_plug = RAGPlug(
      documents=[{"content": d.page_content, "metadata": d.metadata} for d in docs],
      source_name="wiki-v2",
  )
  ctx.plug(rag_plug, scope="company/knowledge")
  ```
- **Import from PowerMem**:
  ```python
  from contextseek.plugs import PowerMemPlug

  # PowerMemPlug.from_records() accepts dicts from PowerMem get_all/search results
  records = powermem_instance.get_all(user_id="shared")  # yields list of dicts
  plug = PowerMemPlug.from_records(records, source_prefix="powermem")
  ctx.plug(plug, scope="company/support-history")
  ```
- **Run compact after bulk import** to consolidate and promote stages before the agent goes live:
  ```python
  ctx.compact(scope="company/knowledge")
  ```
- **Combine pre-populated knowledge with live agent writes** — plug for the initial corpus, then deploy the agent with `ContextSeekMiddleware` writing new Q+A pairs into the same scope. The two pipelines are additive.
- **Lessons learned**: `plug()` is for one-time or scheduled batch ingestion outside the agent loop. `ContextSeekMiddleware` handles continuous, per-turn ingestion inside the agent loop. Use both: `plug()` to seed the store, middleware to keep it growing. Run `compact()` after large bulk imports before the first retrieval to maximize retrieval quality.

**Common configuration problems for this scenario** → see [contextseek-params.md](contextseek-params.md): DataPlug vs manual ctx.add() — which to use for bulk import; plug() scope priority and stage inference.
