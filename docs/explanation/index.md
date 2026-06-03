---
title: Explanation — understanding agentseek
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - docs/index.md
  - docs/blog/introducing-agentseek.md
  - src/agentseek/env.py
  - pyproject.toml
---

# Explanation

> **In short:** these pages tell you *why* agentseek looks the way it does — what it is,
> how it relates to Bub, what flows through the runtime, and how to decide between the
> entry points and extension points on offer.

Explanation pages are discursive. They do not walk you through tasks (that is what
[Tutorials](../tutorials/index.md) are for, and they are not the canonical
fact list (use [Reference](../reference/index.md) when you need exact values).
Read them when a how-to feels mechanical and you want to know why the shape is what it is.

## Pages in this group

| Page | Read it when |
| --- | --- |
| [What agentseek is](what-agentseek-is.md) | You are evaluating the project and need a one-page framing: database-native harness, the two-package split (`agentseek-cli` and `agentseek`), and the explicit non-goals. |
| [Bub relationship](bub-relationship.md) | You want to know how `agentseek` and `bub` divide the work, why the alias model exists, and when to drop down to `bub` directly. |
| [LangChain relationship](langchain-relationship.md) | You already use LangChain / LangGraph / DeepAgents and want to understand how AgentSeek complements the ecosystem — what it adds, what it does not replace, and which template to pick. |
| [Runtime data model](runtime-data-model.md) | You are about to write a plugin, skill, or tape consumer and you need a mental model of tapes, skills, MCP, plugins, and channels. |
| [Extension model](extension-model.md) | You want to extend the runtime and need the decision matrix between instructions, skills, plugins, MCP, and contrib packages before opening a how-to. |
| [Choosing an entry point](choosing-an-entry-point.md) | You are choosing between Path A (`agentseek-cli`), Path B (`agentseek` after `uv sync`), Docker Compose, or a contrib package. |
| [Where things live](where-things-live.md) | You are navigating the monorepo for the first time and want an annotated map of `src/`, `contrib/`, `examples/`, `templates/`, `skills/`, `references/`, and `docs/`. |

## What is not covered here

- Step-by-step instructions to make something run — see
  [Tutorials](../tutorials/index.md) and
  [How-to guides](../how-to/index.md).
- Exhaustive listings of environment variables, CLI flags, file paths, optional extras, or
  templates — see [Reference](../reference/index.md).
- Setup, configuration, and runtime behaviour for contrib packages — every contrib package
  owns its own README (see [contrib packages](https://github.com/ob-labs/agentseek/tree/main/contrib)). Explanation
  pages link out, never duplicate.

## Suggested reading order

1. [What agentseek is](what-agentseek-is.md) for the framing.
2. [Bub relationship](bub-relationship.md) for the kernel layering.
3. [LangChain relationship](langchain-relationship.md) if you come from the LangChain ecosystem.
4. [Runtime data model](runtime-data-model.md) for the substrate.
5. [Extension model](extension-model.md) and
   [Choosing an entry point](choosing-an-entry-point.md) when you are about to build.
6. [Where things live](where-things-live.md) as a reference map you return to.
