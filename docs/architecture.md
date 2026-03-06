# Architecture

This page describes the design boundaries, command model, locking semantics, and cache behavior of bubseek.

## Design boundaries

- **No fork of Bub** — Bub’s core and runtime are unchanged. bubseek is a wrapper distribution.
- **Reuse Bub’s interface** — Commands like `chat`, `run`, `message` are forwarded to Bub.
- **Distribution only in bubseek** — Responsibility for manifest, lockfile, and syncing contrib/skills stays in bubseek:
  - `init` — Initialize or update the manifest (and optionally lock).
  - `lock` — Generate the lockfile from the current config.
  - `sync` — Apply the lockfile (install contrib, copy skills).

## Command model

The CLI surface is kept small:

| Command         | Purpose |
|-----------------|--------|
| `bubseek init`  | Create or update `bubseek.toml`; optional `--with-lock` to run lock after. |
| `bubseek lock`  | Resolve sources and write `bubseek.lock`. |
| `bubseek sync`  | Install contrib and sync skills from the lock into a workspace. |
| `bubseek <any>` | Any other subcommand is forwarded to Bub. |

So all of `bubseek chat`, `bubseek run ...`, `bubseek hooks`, etc. are executed by Bub.

## Locking model

- **Single lockfile** — `bubseek lock` produces one `bubseek.lock` for the whole distribution.
- **Contrib and remote skills** — Locked to a resolved git commit and a source hash.
- **Local bub / contrib / skills** — Locked by content hash (package or directory).
- **Sync guard** — `bubseek sync` checks that the lock matches the current `bubseek.toml` (e.g. config checksum) before installing.

The lockfile records both the pinned `source` and an explicit `resolved_commit` for remote git entries to support auditing and review.

## Sync semantics

`bubseek sync` reads the lockfile and:

1. **Bub + contrib** — Installs locked Bub and contrib packages into the current environment (e.g. via `uv pip install` with locked paths or cached git sources).
2. **Local skills** — Copies from the distribution tree into `<workspace>/.agents/skills/<name>/`.
3. **Remote skills** — Ensures the repo is available (clone or cache), then copies the resolved tree into the workspace skills directory.

Flags:

- `--no-contrib` — Skip contrib installation.
- `--no-skills` — Skip skill sync.
- `--overwrite-skills` — Overwrite existing skill directories in the workspace.

## Cache

Remote git sources are reused across contrib installation and remote skill sync:

- **Default cache root:** `~/.cache/bubseek`
- **Override:** set `BUBSEEK_CACHE_DIR` to a custom path

Shared repos and refs are stored once and reused, so repeated syncs and multiple entries pointing at the same repo/ref avoid duplicate clones.

## Known limitations

- Sync does not yet enforce strict verification of lock hashes for all operations; it uses the lock’s source/path to perform installs and copies.
- Remote skills require Git and network access to the repo.
- Concurrency and cache eviction are not yet optimized; correctness and clarity are prioritized.
