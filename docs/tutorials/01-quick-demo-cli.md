---
title: 01 — Quick demo via the CLI
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.md
---

# Quick demo via the CLI

> **You will:** clone the repository, install dependencies, point agentseek at a model, and
> get one chat turn back from the bundled `agentseek chat` REPL.
> **You need:** Python 3.12+, [uv](https://docs.astral.sh/uv/), `git`, and one model
> provider API key (OpenAI, OpenRouter, DashScope, etc.).

This page exists so you can see that agentseek is real in about five minutes. It is **not**
the recommended way to use agentseek in your own application. The CLI is a Bub-compatible
front door that loads the repository's own configuration; for embedding agentseek in your
own project, jump to `02-first-harness-app.md` after you finish here.

## 1. Clone and install

Get the repository onto your machine and let `uv` resolve the lockfile.

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
```

`uv sync` creates `.venv/` in the repository root and installs the `agentseek` distribution
in editable mode along with its transitive dependencies. From now on, `uv run agentseek …`
runs the version of agentseek that lives in this checkout.

Confirm the CLI loads.

```bash
uv run agentseek --help
```

```text title="expected output"
 Usage: agentseek [OPTIONS] COMMAND [ARGS]...

 Batteries-included, hook-first AI framework

 Commands
   run        Start the project locally after completing .env configuration.
   chat
   onboard    Interactively collect plugin configuration and write it to Bub's
              config file.
   gateway    Start message listeners(like telegram).
   install    Install a plugin into Bub's environment, or sync the environment
              if no specifications are provided.
   uninstall  Uninstall a plugin from Bub's environment.
   update     Update selected package or all packages in Bub's environment.
   create     Create a new agent project from a pre-built template.
   build      Build the project into a container image (wraps `docker build` /
              `docker buildx build`).
   deploy     Generate deployment manifests (docker-compose / k8s).
   api        Forward API runtime commands to `agentseek-api` when it is
              installed.
   ctx        ContextSeek — semantic context layer (forwarded to the
              `contextseek` CLI).
   skills     Manage agent skills via the upstream `vercel-labs/skills` CLI.
   login      Authentication related commands
```

You should now see a `Commands` table that lists at least `run`, `chat`, `create`, and
`install`. If you see a Python traceback instead, stop here and fix the import error before
moving on.

## 2. Point agentseek at a model

agentseek reads `AGENTSEEK_*` variables and forwards them to the underlying Bub runtime as
`BUB_*` aliases. The mapping lives in `src/agentseek/env.py` (`apply_agentseek_env_aliases`).
For exact precedence rules, see `../reference/environment.md`.

Export the three variables that matter for a CLI demo:

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-replace-me              # placeholder, replace with a real key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

The API key is a placeholder — agentseek will start without it but the model call will fail
the moment you press Enter. Replace the value with a real key before continuing.

If you prefer a file over shell exports, copy `.env.example` and edit it; agentseek picks up
`.env` automatically via [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

```bash
cp .env.example .env
```

## 3. Start one chat turn

Run the chat REPL.

```bash
uv run agentseek chat
```

```text title="expected output"
INFO     | channel.manager started listening
╭──────────────── Bub ────────────────╮
│ workspace: /…/agentseek             │
│ model: openai:qwen-plus             │
│ internal command prefix: ','        │
│ shell command prefix: ',' at line start (Ctrl-X for shell mode)
│ type ',help' for command list
╰─────────────────────────────────────╯
agentseek >
```

The `model:` line will say whatever you set in step 2 — `openai:qwen-plus` shown above is
just what the local checkout happened to be configured for. Type a short prompt at the
`agentseek >` prompt, press Enter, and you should see a response stream back. Exit with
`Ctrl+D` or by typing `,quit`.

> **Single-shot variant.** If you just want one prompt without dropping into the REPL,
> `uv run agentseek run "summarize this workspace in one sentence"` is available. Note that
> `agentseek run` belongs to the `agentseek-cli` contrib package and is wired through to the
> upstream Bub `run` behaviour; see `../reference/cli.md` for the full surface.

## What you have now

- A working `.venv/` in the repository root with the agentseek distribution installed.
- Three `AGENTSEEK_*` environment variables (or a populated `.env`) pointing at a real model.
- One round-trip from the `agentseek chat` REPL through your model provider.

## Where to go next

- To run agentseek inside *your own* application instead of the bundled CLI, continue with
  `02-first-harness-app.md`. That is the main onboarding path.
- To understand why the demo uses `.agentseek/` for local state and how the alias model
  works, read `../explanation/bub-relationship.md`.
- To look up every CLI flag or environment variable instead of memorising them, see
  `../reference/cli.md` and `../reference/environment.md`.
