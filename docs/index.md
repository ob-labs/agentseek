---
title: agentseek documentation
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - src/agentseek/env.py
  - pyproject.toml
---

# agentseek

agentseek is a **database-native Agent Harness**: a Bub-compatible runtime distribution you
**embed in your own application** so context, tool calls, traces, and feedback land in one
durable, queryable substrate from the first turn.

The harness/library form is the main thread of these docs. The `agentseek` CLI exists to
prove the project works on your machine in five minutes; it is not the product surface.

## Start here

- **Try the CLI demo (5 min)** — clone, install, and run one chat turn against a free model.
  See [`tutorials/01-quick-demo-cli.md`](tutorials/01-quick-demo-cli.md).
- **Embed in your app (15 min)** — scaffold a project from a template, route a turn through
  your own code, and keep the harness in charge of state.
  See [`tutorials/02-first-harness-app.md`](tutorials/02-first-harness-app.md).

If you are not sure which you are, read
[`explanation/what-agentseek-is.md`](explanation/what-agentseek-is.md) first.

## Read by quadrant

The documentation follows the [Diátaxis framework](https://diataxis.fr/). Each page belongs
to exactly one of these four groups. Pick the one that matches what you are doing right now.

| Quadrant | When to use it | Index |
| --- | --- | --- |
| **Tutorials** — learn by doing | You are new and want a guided run that ends in a working setup. | [`tutorials/index.md`](tutorials/index.md) |
| **How-to** — solve a specific task | You already know the system and need the shortest path to an outcome. | [`how-to/index.md`](how-to/index.md) |
| **Reference** — look up exact facts | You need the canonical list of env vars, CLI flags, file paths, or extras. | [`reference/index.md`](reference/index.md) |
| **Explanation** — understand the design | You want to know *why* agentseek looks like this and where it fits next to Bub. | [`explanation/index.md`](explanation/index.md) |

## Where the project lives

agentseek is a monorepo. The core distribution sits under `src/agentseek/`; larger
integrations live under `contrib/` and own their own READMEs; runnable end-to-end examples
live under `examples/`. The annotated map is in
[`explanation/where-things-live.md`](explanation/where-things-live.md).

External references:

- Upstream runtime: <https://github.com/bubbuild/bub>
- Wider ecosystem catalogue: <https://hub.bub.build>
- Project background: [`blog/introducing-agentseek.md`](blog/introducing-agentseek.md)
