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
[`../tutorials/index.md`](../tutorials/index.md) is for) and they are not the canonical
fact list (use [`../reference/index.md`](../reference/index.md) when you need exact values).
Read them when a how-to feels mechanical and you want to know why the shape is what it is.

## Pages in this group

| Page | Read it when |
| --- | --- |
| [`what-agentseek-is.md`](what-agentseek-is.md) | You are evaluating the project and need a one-page framing: database-native harness, the two-package split (`agentseek-cli` and `agentseek`), and the explicit non-goals. |
| [`bub-relationship.md`](bub-relationship.md) | You want to know how `agentseek` and `bub` divide the work, why the alias model exists, and when to drop down to `bub` directly. |
| [`runtime-data-model.md`](runtime-data-model.md) | You are about to write a plugin, skill, or tape consumer and you need a mental model of tapes, skills, MCP, plugins, and channels. |
| [`extension-model.md`](extension-model.md) | You want to extend the runtime and need the decision matrix between instructions, skills, plugins, MCP, and contrib packages before opening a how-to. |
| [`choosing-an-entry-point.md`](choosing-an-entry-point.md) | You are choosing between Path A (`agentseek-cli`), Path B (`agentseek` after `uv sync`), Docker Compose, or a contrib package. |
| [`where-things-live.md`](where-things-live.md) | You are navigating the monorepo for the first time and want an annotated map of `src/`, `contrib/`, `examples/`, `templates/`, `skills/`, `references/`, and `docs/`. |

## What is not covered here

- Step-by-step instructions to make something run — see
  [`../tutorials/index.md`](../tutorials/index.md) and
  [`../how-to/index.md`](../how-to/index.md).
- Exhaustive listings of environment variables, CLI flags, file paths, optional extras, or
  templates — see [`../reference/index.md`](../reference/index.md).
- Setup, configuration, and runtime behaviour for contrib packages — every contrib package
  owns its own README (see [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib)). Explanation
  pages link out, never duplicate.

## Suggested reading order

1. [`what-agentseek-is.md`](what-agentseek-is.md) for the framing.
2. [`bub-relationship.md`](bub-relationship.md) for the layering.
3. [`runtime-data-model.md`](runtime-data-model.md) for the substrate.
4. [`extension-model.md`](extension-model.md) and
   [`choosing-an-entry-point.md`](choosing-an-entry-point.md) when you are about to build.
5. [`where-things-live.md`](where-things-live.md) as a reference map you return to.
