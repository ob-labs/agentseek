---
hide_sidebar: true
---

# AgentSeek

AgentSeek is a database-native Agent Harness for teams that want agent runtime
data to become a first-class database workload. LangChain is the recommended
way to start building on it.

> **Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), and a
> model provider API key. That's it.

**AgentSeek is a suite** of components that work independently or together:

| Component | What it does | Docs |
| --- | --- | --- |
| **agentseek-cli** | Scaffold projects, manage lifecycle (`create / run / build / deploy`) | [ob-labs/agentseek](https://github.com/ob-labs/agentseek) |
| **agentseek-api** | Agent Protocol server — ship your LangGraph to production, zero code change | [ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| **ContextSeek** | Semantic context layer — memory, retrieval, evolution, progressive disclosure | [ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| **langchain-oceanbase** | Data substrate — checkpoint + store + vector + hybrid search on OceanBase / seekdb / MySQL | [oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |

---

## Quick Start — for LangChain developers

**Which template should I pick?**

- **Starting fresh / learning?** → `langchain/markdown-messages` (minimal, 5 min)
- **Already have a graph, need to deliver a product?** → `langchain/default` (frontend + Feishu IM + full runtime)
- **Need deep research with sub-agents?** → `deepagents/research` (Tavily + report generation)
- **Graph runs on a remote server (agentseek-api / LangSmith)?** → `langchain/cli-remote`

```bash
# Pick one and run:
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
# or: langchain --template default
# or: deepagents --template research
```

Then: `cd <project> && uv sync && uv run langgraph dev` (minimal) or
`uv run agentseek run` (full delivery).

> **LangSmith tracing is pre-configured.** Every template ships a `.env.example`
> with `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` ready to fill in. Set
> your key and you get full run observability in LangSmith immediately.

**Next steps after your agent runs:**

- Add persistent memory → [ContextSeek docs](https://github.com/ob-labs/contextseek)
- Ship to production as a service → [agentseek-api docs](https://github.com/ob-labs/agentseek-api)
- Switch to a durable database → [langchain-oceanbase docs](https://github.com/oceanbase/langchain-oceanbase)
- Install dev skills for guided help → see [Development skills](#development-skills) below
- Study DeepAgents systematically → see [Open-source course](#open-source-course) below
- Understand the full relationship → [How agentseek relates to LangChain](explanation/langchain-relationship.md)

---

## For OceanBase / seekdb / MySQL developers

Already running OceanBase, seekdb, or MySQL? AgentSeek uses your database as
the **data substrate** for AI agents — checkpoint, persistent memory, vector
search, and hybrid retrieval all run on the DB you already operate.

```bash
pip install langchain-oceanbase[pyseekdb]   # OceanBase / seekdb
pip install langchain-oceanbase             # MySQL (checkpoint + store)
```

This gives you:

- **LangGraph Checkpoint** — durable execution state for long-running agents
- **Store** — cross-session persistent memory (namespaced key-value)
- **VectorStore + Hybrid Search** — embedding retrieval fused with BM25 (OceanBase / seekdb)

MySQL users get checkpoint and store out of the box; vector search requires
OceanBase or seekdb. Either way, runtime data is queryable SQL from day one.

**Get started:**

1. Install: `pip install langchain-oceanbase[pyseekdb]`
2. Read the integration guide: [langchain-oceanbase README](https://github.com/oceanbase/langchain-oceanbase#readme)
3. Pick a template to run a full agent on top: `agentseek create langchain --template default`
4. For the harness tape store plugin: see [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)

---

## New to agents? Start here

Never built an AI agent before? No problem.

1. Make sure you have Python 3.12+ and [uv](https://docs.astral.sh/uv/) installed
2. Get a model API key (OpenRouter free tier works: [openrouter.ai](https://openrouter.ai))
3. Run:

```bash
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
cd markdown_messages_agent
cp .env.example .env   # fill in your API key
uv sync && uv run langgraph dev
```

You now have a chatbot running locally. Open the URL printed in the terminal.

**Where to go from here:**

- [Quick demo tutorial](tutorials/01-quick-demo-cli.md) — 5-minute walkthrough with screenshots
- [Build your first harness app](tutorials/02-first-harness-app.md) — full tutorial with frontend

---

## The suite in action

### agentseek-api — ship your graph to production

```bash
uv run agentseek-api dev
curl http://127.0.0.1:2024/info
```

Implements the [Agent Protocol](https://github.com/langchain-ai/agent-protocol)
(threads, runs, streaming, Store API, MCP, A2A). Your LangGraph code runs
unchanged behind standard HTTP endpoints.

Full docs: [github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api)

### ContextSeek — semantic context layer

```python
from contextseek import ContextSeek

ctx = ContextSeek.from_settings()
ctx.add("OceanBase is a distributed database for financial workloads",
        scope="acme/db", source="wiki")

for hit in ctx.retrieve("distributed database", scope="acme/db", k=5):
    print(hit.item.stage, hit.score, hit.item.summary[:60])
```

Unified `ContextItem` model with provenance, L0/L1/L2 progressive disclosure,
EvolutionEngine, DreamEngine. Accessible via HTTP, MCP, or Python SDK. Ships
with a **LangChain middleware** for automatic context injection per turn and
**LangSmith `@traceable` support** for full observability.

Full docs: [github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek)

### langchain-oceanbase — the data substrate

```bash
pip install langchain-oceanbase[pyseekdb]
```

LangGraph Checkpoint + Store + VectorStore + Hybrid Search — all on one
database (OceanBase, seekdb, or MySQL). Runtime data is queryable SQL from day
one.

Full docs: [github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)

---

## Open-source course

Want to learn DeepAgents from the ground up? The free course
**"Deep Agents 实战"** (Deep Agents in Action) teaches you to build
production-grade AI agents with LangChain / LangGraph / DeepAgents — and uses
AgentSeek for all hands-on labs.

| Resource | Link |
| --- | --- |
| Course site | [webup.github.io/deepagents-course](https://webup.github.io/deepagents-course) |
| Video playlist (Bilibili) | [B站合集](https://space.bilibili.com/28357052/lists/7757577?type=season) |
| Source repo | [github.com/webup/deepagents-site](https://github.com/webup/deepagents-site) |

Topics covered: Agent Harness concepts, virtual filesystem, task planning,
sub-agents, async delegation, long-term memory, Human-in-the-Loop, skills,
sandboxes, streaming frontends, and production deployment — all built on
AgentSeek templates.

---

## Development skills

AgentSeek ships a set of **development skills** — installable guides that live
inside your AI coding agent (Claude Code, Cursor, etc.) and help you build
LangChain applications without leaving the editor.

| Skill | What it does |
| --- | --- |
| **langchain-dev-guide** | Engineering pitfalls and verified fixes for LangChain / LangGraph. Covers DeepAgents, middleware, streaming, multi-agent orchestration, and common issues — each with Symptom → Cause → Solution. |
| **langchain-cn-models** | Step-by-step recipes for integrating Chinese LLM providers (DeepSeek, Qwen, GLM, Moonshot, etc.) into LangChain via the OpenAI-compatible interface. |

Install all skills at once:

```bash
npx skills add ob-labs/agentseek --all
```

Or pick specific ones:

```bash
npx skills add ob-labs/agentseek --skill langchain-dev-guide --agent claude-code
npx skills add ob-labs/agentseek --skill langchain-cn-models --agent claude-code
```

Once installed, your coding agent can reference these guides when you hit a
LangChain issue — no manual doc searching needed.

Full details: [skills/](https://github.com/ob-labs/agentseek/tree/main/skills)
| How to add skills: [Add skills guide](how-to/add-skills.md)

---

## Other paths

**Already using [Bub](https://github.com/bubbuild/bub)?** AgentSeek is a
distribution of Bub with opinionated defaults. Try
`agentseek create bub --template default` for CopilotKit + Feishu without
LangChain. See [How agentseek relates to Bub](explanation/bub-relationship.md).

**Want the raw harness CLI?** See
[Choosing an entry point](explanation/choosing-an-entry-point.md).

## Read next

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">Documentation</a></h3>
    <p>Architecture, design rationale, and how the docs are organized.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="tutorials/">Tutorials</a></h3>
    <p>Guided walkthroughs: quick demo, first app, adding skills and MCP.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">How-to guides</a></h3>
    <p>Task-focused recipes: configure models, deploy, run gateway, use ContextSeek.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">Reference</a></h3>
    <p>Environment variables, CLI, packages, templates, file layout, Docker.</p>
  </div>
</div>
