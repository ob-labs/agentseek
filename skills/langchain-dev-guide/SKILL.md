---
name: langchain-dev-guide
description: "LangChain / LangGraph engineering pitfalls and verified fixes. Covers DeepAgents, OpenAI-compatible model integration, middleware, streaming, multi-agent orchestration, and other common development issues. Use when hitting unexpected behavior or making architecture decisions during LangChain development."
---

# LangChain Dev Guide

A systematic summary of typical issues, non-obvious behaviors, and verified solutions encountered in real engineering with the LangChain / LangGraph ecosystem. Every entry comes from a real development scenario and is organized by category.

> [!IMPORTANT]
> This skill is an **engineering practice reference**, not an introductory tutorial. Each entry assumes the developer is already familiar with basic LangChain concepts (agent, tool, message, graph).

## How to Use

1. First use the "Scenario Index" below to locate the category file your problem belongs to.
2. When unsure which category applies, search keywords directly in the "Common Issues Quick Reference".
3. For ContextSeek / semantic memory: start with [contextseek-middleware.md](reference/contextseek-middleware.md) to identify your scenario, then go to [contextseek-params.md](reference/contextseek-params.md) for specific parameter configuration issues.
4. Once you find the relevant section, read it in depth — every entry follows the structure **Symptom → Cause → Solution → Lessons learned**.

## Scenario Index

| Category | File | Trigger Scenarios |
|----------|------|-------------------|
| Deep Agents | [reference/deepagents.md](reference/deepagents.md) | Model selection, filesystem backend, disabling the general-purpose sub-agent, file permissions, long-term memory |
| OpenAI-compatible Model Integration | [reference/model-integration.md](reference/model-integration.md) | Pitfalls when using `ChatOpenAI` against OpenAI-compatible providers, integrating Reasoning models (chain-of-thought / `reasoning_content`) |
| Middleware | [reference/middleware.md](reference/middleware.md) | Middleware execution order, `state_schema` merging, HITL `resume` values, modifying state from `wrap_model_call` |
| Streaming Output | [reference/streaming.md](reference/streaming.md) | Choosing between `stream_events` and `stream`, distinguishing tokens from multiple LLMs, disabling streaming, custom progress events |
| Multi-Agent Orchestration | [reference/multi-agent.md](reference/multi-agent.md) | subagents vs handoffs, tool-per-agent vs dispatch, retrieving subagent state, trimming subagent boilerplate, quickly building handoff setups |
| Other Common Issues | [reference/common-issues.md](reference/common-issues.md) | High-frequency standalone issues that don't fit the categories above. Currently includes: tools returning data to both the model and the application layer, `with_structured_output` returning None, MCP tools unable to access runtime context |
| ContextSeek — Use Case Scenarios | [reference/contextseek-middleware.md](reference/contextseek-middleware.md) | Agent loses context across sessions, tool call auditing, cross-topic knowledge discovery (dream), SRE provenance / confidence tracing, enterprise knowledge cold-start (DataPlug) |
| ContextSeek — Parameter & Config Issues | [reference/contextseek-params.md](reference/contextseek-params.md) | scope isolation, auto_store / record_tool_calls write volume, auto_compact throttling and shutdown, retrieval_tags / min_score filtering, tool_arg_overrides, dream trigger conditions, dream item decay, evidence_chain vs chain_confidence, DataPlug vs ctx.add(), plug() scope priority, auto_dream dual-gate triggering |

## Common Issues Quick Reference

| Keyword / Error | Where to Look |
|-----------------|---------------|
| Which model to choose / Deep Agent performing poorly | deepagents issue 1 |
| Filesystem backend / local files / file permissions | deepagents issues 2 / 4 |
| Disabling the default sub-agent / general-purpose | deepagents issue 3 |
| Long-term memory / store | deepagents issue 5 |
| OpenAI-compatible model / `ChatOpenAI` not working | model-integration issue 1 |
| Reasoning model / `reasoning_content` / chain-of-thought lost | model-integration issue 2 |
| Middleware order messed up / before/after counterintuitive | middleware issue 1 |
| `state_schema` fields not merged / input/output control | middleware issue 2 |
| `interrupt` resume value missing / HITL | middleware issue 3 |
| Modifying state inside `wrap_model_call` has no effect | middleware issue 4 |
| Choosing between `astream_events` and `astream` for streaming | streaming issue 1 |
| Distinguishing token sources across multiple LLMs | streaming issue 2 |
| Disabling streaming for a specific model | streaming issue 3 |
| Custom events from inside a tool not being emitted | streaming issue 4 |
| Multi-agent: subagents vs handoffs | multi-agent issue 1 |
| Single dispatch tool vs one tool per agent | multi-agent issue 2 |
| `interrupt` can't see subagent state | multi-agent issue 3 |
| Too much subagent wrapper boilerplate | multi-agent issue 4 |
| Quickly building a handoff-based multi-agent setup | multi-agent issue 5 |
| Tool returning data to both the model and the app layer / `artifact` / `Command(update=...)` | common-issues issue 1 |
| `with_structured_output` returning None / missing fields | common-issues issue 2 |
| MCP tool can't access `user_id` / `store` / state / API key | common-issues issue 3 |
| Agent loses context across sessions — personal assistant or support bot | contextseek-middleware issue 1 |
| Multi-tool data-pipeline agent — auditing tool call decisions | contextseek-middleware issue 2 |
| Research agent accumulates raw notes — cross-topic pattern discovery | contextseek-middleware issue 3 |
| SRE incident postmortem agent — tracing knowledge confidence and conflicts | contextseek-middleware issue 4 |
| Enterprise knowledge migration — agent is retrieval-ready on day one | contextseek-middleware issue 5 |
