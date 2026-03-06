# bubseek

[![PyPI version](https://img.shields.io/pypi/v/bubseek.svg)](https://pypi.org/project/bubseek/)
[![License](https://img.shields.io/github/license/psiace/bubseek.svg)](LICENSE)
[![CI](https://github.com/psiace/bubseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/psiace/bubseek/actions/workflows/main.yml?query=branch%3Amain)

**Enterprise-oriented distribution of [Bub](https://github.com/bubbuild/bub)** for agent-driven insight workflows in cloud-edge environments.

bubseek turns fragmented data across operational systems, repositories, and agent runtime traces into **explainable, actionable, and shareable insights** without heavy ETL. It keeps the Bub runtime and extension model while adding distribution tooling: declarative config, lockfiles, and sync for contrib packages and skills.

## Features

- **Lightweight and on-demand** — Trigger analysis when needed instead of maintaining large offline pipelines.
- **Explainability first** — Conclusions are returned together with agent reasoning context.
- **Cloud-edge ready** — Supports distributed deployment and local execution boundaries.
- **Agent observability** — Treats agent behavior as governed, inspectable runtime data.
- **Bub-compatible** — Forwards all non-bubseek commands to Bub; no fork of the core runtime.

## Installation

Requires [uv](https://docs.astral.sh/uv/) (recommended) or pip, and Python 3.12+.

From the project root:

```bash
git clone https://github.com/psiace/bubseek.git
cd bubseek
uv sync
```

Or install from PyPI (when published):

```bash
uv add bubseek
```

## Quick start

1. **Initialize** a manifest and lockfile (or use the existing `bubseek.toml`):

   ```bash
   uv run bubseek init --with-lock
   ```

2. **Regenerate the lockfile** after editing `bubseek.toml`:

   ```bash
   uv run bubseek lock
   ```

3. **Sync** locked contrib packages and skills into a workspace:

   ```bash
   uv run bubseek sync --workspace .
   ```

4. **Run Bub** via bubseek (all other commands are forwarded to Bub):

   ```bash
   uv run bubseek chat
   uv run bubseek run ",help"
   ```

   If your Bub runtime or model plugin expects API credentials, put them in `.env`.
   `bubseek` forwards `.env` values to the `bub` subprocess as-is.

   ```dotenv
   bub_api_key=sk-or-v1-...
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   ```

## Commands

| Command        | Description                                      |
|----------------|--------------------------------------------------|
| `bubseek init` | Create or update `bubseek.toml` (optional lock). |
| `bubseek lock` | Generate or update `bubseek.lock` from config. |
| `bubseek sync` | Install Bub/contrib and sync skills from the lock. |
| `bubseek *` | Any other subcommand is passed through to Bub. |

## Repository layout

```
bubseek/
├── bubseek.toml      # Distribution manifest (bub, contrib, skills)
├── bubseek.lock      # Generated lockfile (commit this)
├── src/bubseek/      # Package source
├── skills/           # Bundled skills
├── contrib/          # Contrib metadata and notes
├── docs/             # Documentation
└── tests/
```

See [Configuration](https://psiace.github.io/bubseek/configuration/) for the full `bubseek.toml` reference.

## Documentation

- [Getting started](https://psiace.github.io/bubseek/getting-started/) — Install, init, lock, sync.
- [Configuration](https://psiace.github.io/bubseek/configuration/) — `bubseek.toml` and locking.
- [Architecture](https://psiace.github.io/bubseek/architecture/) — Design and sync semantics.
- [API reference](https://psiace.github.io/bubseek/api-reference/) — Python API.
- [Development](https://psiace.github.io/bubseek/development/) — Tests, linting, contributing.

## Development

```bash
make install   # Create venv and install pre-commit
make check     # Lint and type-check
make test      # Run pytest
make docs      # Serve MkDocs locally
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

[Apache-2.0](LICENSE).
