---
title: Choosing an entry point
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli.py
  - entrypoint.sh
  - contrib/README.md
  - examples/README.md
---

# Choosing an entry point

> **In short:** agentseek has four entry points — **library** (embed it in your app), the
> **`agentseek` CLI**, **Docker Compose**, and **contrib packages**. The recommended path
> for application developers is the library; everything else is a wrapper around the same
> framework.

## Context

People meet agentseek in different ways. Evaluators want a one-command demo. Application
developers want to drop the harness into a service they already own. Operators want a
container they can mount a workspace into. Plugin authors want to pick up an existing
contrib package or scaffold a new one. The four entry points exist so each of those flows
has a sharp starting point — but it is easy to mistake the demo entry for the product.
This page resolves that.

## How it works

### Library — the recommended path

Depend on `agentseek` as a regular Python distribution
(`pyproject.toml:2` declares the project name) and drive the framework from your own code.
Booting the framework is exactly what `src/agentseek/__main__.py:52-69` does for the CLI:

1. Call `apply_agentseek_env_aliases()` and `apply_agentseek_cli_overrides()` (or skip the
   CLI overrides if you do not need them).
2. Construct `BubFramework(config_file=agentseek_config_file())`.
3. Call `load_hooks()` and route turns through whichever channel you need.

This is the surface tutorials and how-tos are written for. The library form gives you:

- Full control over how a turn is dispatched (your app picks the channel, the lifecycle,
  the request shape).
- The ability to keep your existing framework code (LangChain, DeepAgents, your own
  orchestrator) and route model turns through `agentseek-langchain` while the harness owns
  state.
- The same tape, plugin, and MCP behaviour as every other entry point — because every
  other entry point boots the same framework.

Project templates under `templates/` (see [`../reference/templates.md`](../reference/templates.md))
exist to skip the boilerplate. The end-to-end app tutorial is
[`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md).

### CLI — the quick demo

`agentseek …` is a Typer app produced by `BubFramework.create_cli_app()`
(`src/agentseek/__main__.py:52-66`). It exposes Bub's builtin commands plus contrib
subcommands, with three deliberate overrides from `src/agentseek/cli.py:74-152`:

- the onboarding banner reads `AGENTSEEK`,
- `chat` enables lifecycle channels so MCP and friends boot,
- `install` uses the agentseek-named plugin sandbox.

Use the CLI when you are:

- **Evaluating** the project. `agentseek chat` against a free model in five minutes is the
  whole point of [`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md).
- **Operating** a workspace. `agentseek run`, `agentseek gateway`, `agentseek install`, and
  the contrib-supplied lifecycle commands (`agentseek create`, `build`, `deploy`, `api`,
  `ctx`, `skills`) are real ops surface; the catalogue is in
  [`../reference/cli.md`](../reference/cli.md).
- **Debugging** harness behaviour next to a Bub Hub example.

The CLI is **not** the place to build an application around. Anything you would put in a
shell pipeline can usually be expressed more cleanly by depending on the library and
calling the framework directly.

### Docker Compose — the operator path

`entrypoint.sh:5-26` resolves `BUB_*`/`AGENTSEEK_*` pairs, exports both, ensures the home
and project directories exist, optionally symlinks `.agents/skills` and `.agents/mcp.json`
into the runtime paths (`entrypoint.sh:30-39`), and finally execs either a
workspace-provided `startup.sh` or `agentseek gateway` (`entrypoint.sh:41-45`).

Use Compose when you want a **mounted workspace** plus a long-running gateway, without
managing a Python environment on the host. The default mounts the current repository at
`/workspace`, keeps `.agents/skills` and `.agents/mcp.json` available, and persists runtime
state under `.agentseek/` in the workspace (see the Quick Start section of
[`README.md`](https://github.com/ob-labs/agentseek/blob/main/README.md) for the user-facing commands;
[`../how-to/run-with-docker-compose.md`](../how-to/run-with-docker-compose.md) is the
canonical walkthrough).

Compose is still the library form under the hood — `entrypoint.sh` just sets up env and
mounts before launching `agentseek gateway`. If you have a custom service, you can drop a
`startup.sh` into the workspace and the entrypoint will exec it instead.

### Contrib packages — feature-scoped entry points

Each `contrib/agentseek-*/` package is a Python distribution you can install on top of the
core. They are listed at [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib) and exposed
as optional extras under `pyproject.toml:27-46`. The two that act like entry points in
their own right are:

- **`agentseek-cli`** — adds the project-lifecycle commands (`create / run / build /
  deploy / api / ctx / skills`). You can install it as an extra
  (`uv sync --extra cli`) to fold those commands into `agentseek …`, or run it standalone
  via `uvx agentseek-cli` when you do not want it touching the main environment.
- **`agentseek-ag-ui`** — adds the AG-UI SSE channel for `agentseek gateway`, which is the
  bridge to CopilotKit-style front-ends. The end-to-end shape is shown in the
  [`examples/ag-ui`](https://github.com/ob-labs/agentseek/tree/main/examples/ag-ui) example.

Other contrib packages (`agentseek-langchain`, `agentseek-tapestore-oceanbase`,
`agentseek-observability`, `agentseek-schedule-sqlalchemy`, `agentseek-contextseek`) are
runtime plugins rather than entry points; they extend the framework that the library, CLI,
and Compose paths all share. See [`extension-model.md`](extension-model.md).

## Why it is like this

- **Library first.** The harness is meant to host application code. Putting the library at
  the centre keeps every other entry point honest: they have to be implementable on top of
  the same framework, which they are.
- **CLI as proof-of-life.** A five-minute demo is the cheapest way to show the project
  works on a stranger's machine. Pitching the CLI as the product would push application
  developers toward shell glue and away from the library.
- **Compose for operators.** A single `make compose-up` against a mounted workspace is the
  fastest way to get someone else's checkout running with the same defaults. The
  entrypoint deliberately only sets env, ensures paths, and execs — no magic.
- **Contrib as opt-in feature surface.** Each contrib package owns its own dependency tree
  and documentation; the core distribution stays small. Extras in `pyproject.toml` are how
  the project advertises that surface without forcing it on everyone.

## Consequences for users

- If you are an **application developer (A2)**, start with the library tutorial
  ([`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)). The
  CLI demo ([`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md)) is a
  one-time sanity check before you commit to the library form.
- If you are an **evaluator (A1)**, the CLI demo is the right starting point and the
  library tutorial is optional.
- If you are an **operator (A4)**, Compose is the right starting point; the CLI is your
  inner-loop tool for poking at the runtime.
- If you are a **plugin author (A3)**, you embed your plugin into the same Python
  environment that all four entry points share. Test under both `agentseek` and `bub`
  (see [`bub-relationship.md`](bub-relationship.md)) to catch accidental coupling to
  agentseek defaults.
- Anywhere you mix paths — for example, running the CLI in development and Compose in
  staging — the framework underneath is the same, but the env var resolution differs
  slightly. The full table is in [`../reference/environment.md`](../reference/environment.md).

## Related

- Tutorial: [`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md),
  [`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)
- How-to: [`../how-to/run-locally.md`](../how-to/run-locally.md),
  [`../how-to/run-with-docker-compose.md`](../how-to/run-with-docker-compose.md),
  [`../how-to/install-a-plugin.md`](../how-to/install-a-plugin.md)
- Reference: [`../reference/cli.md`](../reference/cli.md),
  [`../reference/packages.md`](../reference/packages.md),
  [`../reference/docker.md`](../reference/docker.md),
  [`../reference/templates.md`](../reference/templates.md)
- Explanation: [`what-agentseek-is.md`](what-agentseek-is.md),
  [`bub-relationship.md`](bub-relationship.md),
  [`where-things-live.md`](where-things-live.md)
