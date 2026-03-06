# Getting started

This guide walks you through installing bubseek, creating or using a manifest, locking dependencies, and syncing contrib packages and skills.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **Git** (for remote contrib and skills)

## Installation

From the bubseek repository root:

```bash
git clone https://github.com/psiace/bubseek.git
cd bubseek
uv sync
```

This creates a virtual environment and installs bubseek and its dependencies (including Bub from the configured branch).

Verify:

```bash
uv run bubseek --help
```

## Initialize a manifest

If you are in a fresh or existing repo and want a `bubseek.toml` and optional lockfile:

```bash
uv run bubseek init --with-lock
```

You can customize contrib packages and repo:

```bash
uv run bubseek init --contrib bub-codex --contrib bub-schedule --contrib-repo https://github.com/bubbuild/bub-contrib --with-lock
```

Edit `bubseek.toml` to add or change `[bub]`, `[[contrib]]`, and `[[skills]]` entries. See [Configuration](configuration.md).

## Lock

After editing `bubseek.toml`, regenerate the lockfile:

```bash
uv run bubseek lock
```

Optionally pass a config path:

```bash
uv run bubseek lock --config path/to/bubseek.toml
```

The lockfile records resolved git commits and content hashes so that `bubseek sync` is reproducible.

## Sync

Install locked contrib packages and sync skills into a workspace:

```bash
uv run bubseek sync --workspace .
```

- **Contrib** packages are installed into the current environment (e.g. via `uv pip install` with locked sources).
- **Skills** are copied into `<workspace>/.agents/skills/<name>/`.

Skip one side if needed:

```bash
uv run bubseek sync --workspace . --no-contrib
uv run bubseek sync --workspace . --no-skills
```

Overwrite existing workspace skills:

```bash
uv run bubseek sync --workspace . --overwrite-skills
```

## Run Bub

Any command that is not `init`, `lock`, or `sync` is forwarded to Bub:

```bash
uv run bubseek chat
uv run bubseek run ",help"
uv run bubseek run "Summarize this repo"
```

Bub runtime behavior (models, API keys, comma commands, etc.) is unchanged; see [Bub](https://github.com/bubbuild/bub) for details.

## Next steps

- [Configuration](configuration.md) — Full `bubseek.toml` reference and locking model.
- [Architecture](architecture.md) — How init/lock/sync and the cache work.
