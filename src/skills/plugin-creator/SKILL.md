---
name: plugin-creator
description: |
  Create or update an agentseek/Bub plugin in any local path. Use when the task is to scaffold a
  Python package that exposes a [project.entry-points.bub] entry, implement Bub hooks or tools,
  and make the plugin take effect by installing it or adding it as a dependency in the agentseek
  runtime project. When working inside agentseek, also follow its contrib layout, packaging
  conventions, and AGENTSEEK_* alias behavior while preserving Bub compatibility.
---

# Agentseek Plugin Creator

Create agentseek plugins as normal Python packages that follow Bub's extension model.

Core rule: a plugin becomes effective only when both conditions are true:

1. the package exposes an entry point in the `bub` group
2. the package is installed in the same Python environment as agentseek/Bub

Agentseek is a Bub-compatible distribution and runtime layer, not a separate plugin system. Keep
Bub hooks, entry-point groups, tool decorators, and runtime contracts compatible unless there is a
clear agentseek-only reason to add an alias or packaging adjustment.

## What Counts As An Agentseek Plugin

An agentseek plugin is usually a Python package with:

- `pyproject.toml`
- `README.md`
- `src/<python_package>/__init__.py`
- `src/<python_package>/plugin.py` or another hook-exporting module such as `tools.py`
- optional helper modules such as `channel.py`, `store.py`, `job_store.py`, `settings.py`, or `config.py`
- optional tests under `tests/` or `src/tests/`, matching the host repository's convention
- optional bundled agent skill files under `src/skills/<skill-name>/`

The package must export a Bub entry point through:

```toml
[project.entry-points.bub]
<plugin-name> = "<python_package>.plugin"
```

Other valid targets also exist, for example:

```toml
[project.entry-points.bub]
<plugin-name> = "<python_package>.tools"
<plugin-name> = "<python_package>.plugin:main"
```

Use the narrowest export surface that matches the implementation.

## First: Identify The Host Project

Before creating files, determine where the plugin should live and where agentseek/Bub runs.

There are three common cases:

1. Existing agentseek monorepo package
   Create a new package inside `contrib/` and wire it into this repository's dependency flow.

2. Standalone local package
   Create a new package in any local path, then install it into the agentseek/Bub environment with
   an editable or path-based dependency.

3. Existing package to extend
   Update the package in place and make sure the environment uses the updated dependency.

Important distinction:

- plugin source location: where files are created
- activation location: the project or environment that installs the package

If the task is ambiguous, infer both from nearby files such as `pyproject.toml`, `uv.lock`,
`.venv`, and how `agentseek` or `bub` is launched.

## Classify The Plugin Shape

Inspect the closest existing plugin before writing code. In this repository, use packages under
`contrib/` as the primary examples.

Common shapes:

1. Channel provider
   Use when the plugin connects agentseek/Bub to an external message source or sink.
   Typical hook: `provide_channels`

2. Hook-only provider
   Use when the plugin contributes one focused hook such as model execution.
   Typical hook: `run_model`

3. Resource provider
   Use when the plugin returns a store or singleton runtime resource.
   Typical hook: `provide_tape_store`

4. Composite plugin
   Use when the plugin owns runtime state and also provides channels or tools.
   Typical hooks: `load_state` plus one or more provider hooks

5. Tool registration package
   Use when the package mainly exposes `@tool` functions and exports the tool module directly.

Prefer copying the nearest existing shape over inventing a new abstraction.

## Implementation Workflow

### 1. Read The Closest Reference

Open the closest existing package first.

Minimum files to inspect:

- host project's `pyproject.toml`
- closest plugin package `pyproject.toml`
- closest plugin entry-point module such as `plugin.py` or `tools.py`
- one or two representative tests
- `README.md`

If the plugin interacts with an agent-facing chat platform, also inspect any packaged skill such as
`src/skills/<skill-name>/SKILL.md`.

### 2. Choose The Package Location

Default structure for a new agentseek-owned package:

```text
contrib/agentseek-<feature>/
├── pyproject.toml
├── README.md
├── src/
│   └── agentseek_<feature>/
│       ├── __init__.py
│       ├── plugin.py or tools.py
│       └── ...
└── src/tests/
    └── test_agentseek_<feature>.py
```

Naming conventions:

- distribution name: use `agentseek-<feature>` for agentseek-owned packages
- Python package: use `agentseek_<feature>` for agentseek-owned packages
- Bub entry point name: prefer the user-facing short name, usually `<feature>`
- entry point group: always `bub`

Treat the `agentseek-*` / `agentseek_*` prefix as the default constraint for new packages created
through this skill. The main reason is to avoid namespace conflicts with upstream Bub packages and
other third-party plugins.

Do not rename existing third-party packages unless the user explicitly asks.

If working outside this repository, create the package in the user-requested path or in the nearest
plugin-oriented subdirectory of the host project.

### 3. Implement Packaging Metadata

`pyproject.toml` should usually include:

- `name`
- `version`
- `description`
- `readme`
- `requires-python`
- runtime `dependencies`
- `[project.entry-points.bub]`
- build backend

Prefer `src/` layout unless the host project clearly uses another convention.

For `uv` workspace activation in this repository, update both:

```toml
[tool.uv.sources]
agentseek-<feature> = { workspace = true }

[tool.uv.workspace]
members = ["contrib/agentseek-<feature>"]
```

Then add the plugin package to the host project's dependencies if it should be enabled by default:

```toml
[project]
dependencies = ["agentseek-<feature>"]
```

Outside this repository, path activation commonly looks like one of these:

```toml
[project]
dependencies = ["agentseek-my-plugin"]

[tool.uv.sources]
agentseek-my-plugin = { path = "../agentseek-my-plugin", editable = true }
```

or:

```bash
uv pip install -e /abs/path/to/agentseek-my-plugin
```

Choose the activation method that matches the host project:

- persistent project dependency: update host `pyproject.toml`
- local development only: editable install may be sufficient
- monorepo workspace: add the package to workspace and source mapping if required

### 4. Implement The Bub Entry Module

Prefer the narrowest hook surface that solves the task.

Common patterns:

- `@hookimpl def provide_channels(...) -> list[Channel]`
- `@hookimpl async def run_model(...) -> str`
- `@hookimpl def provide_tape_store() -> ...`
- `@hookimpl def load_state(...) -> State`
- `@tool(name="...")` in a module exported directly as the Bub entry point

Guidelines:

- Keep the exported entry module thin when possible.
- Move protocol or platform code into helper modules such as `channel.py`, `store.py`, or `tools.py`.
- Use `pydantic-settings` or the host project's config approach when environment variables exist.
- Prefer `AliasChoices("BUB_<FEATURE>_...", "AGENTSEEK_<FEATURE>_...")` when the same setting
  should work in both plain Bub and agentseek. If both prefixes are present, `BUB_*` should win.
- If the host project already uses registered Bub settings via `@bub.config`, preserve that pattern
  and keep runtime access consistent with `bub.ensure_config(...)` instead of mixing direct
  construction and framework-managed config in the same plugin.
- Cache singleton resources only when reuse is intentional and testable.
- Avoid framework-wide abstractions unless at least two packages actually need them.

### 5. Add Optional Agent Skill Files Only When Needed

Create `src/skills/<skill-name>/SKILL.md` only if the plugin exposes agent-facing operational
behavior, for example a chat channel that needs explicit send, edit, or reply instructions.

Do not add a packaged agent skill for internal providers unless there is a real agent workflow to
teach.

If you add packaged skill files:

- keep them specific to the platform or workflow
- make command paths relative to the skill directory
- include scripts under `src/skills/<skill-name>/scripts/`
- make sure packaging includes `SKILL.md` and scripts

### 6. Wire The Plugin Into The Runtime

This step is mandatory. Creating the package alone does not activate it.

Pick one of these activation paths:

1. Add as a normal dependency in the agentseek host project
   Update host `pyproject.toml` dependencies and any source mapping such as `tool.uv.sources`.

2. Add as a workspace package
   Update workspace membership and source mapping so the host environment resolves the plugin.

3. Install directly into the active environment
   Use an editable or normal install such as `uv pip install -e /abs/path/to/plugin`.

When the task says "make it effective", prefer option 1 or 2 over a one-off install unless the
user clearly wants a local experiment.

### 7. Write The Minimum Useful README

Keep the README short and operational. Usually include:

- what the plugin provides
- required environment variables or configuration
- how to install or enable it
- any notable behavior or limitations

Do not pad it with generic packaging tutorials.

### 8. Add Targeted Tests

Non-trivial plugin behavior should have tests.

Favor narrow tests over large integration scaffolding.

Typical coverage:

- entry hook returns the right type or object
- settings parse environment variables correctly
- plugin-level singleton or factory behavior
- fallback and error-path behavior for boundary conditions

Use the host project's test style. In this repository, that usually means:

- `pytest`
- direct imports from `<package>.plugin`
- `monkeypatch` for environment variables and runtime substitution
- `tmp_path` for filesystem behavior

## Decision Rules

- Prefer repository consistency over abstract elegance.
- Prefer one package per plugin, even if the implementation is small.
- Prefer Bub-compatible hook contracts and entry points over agentseek-only abstractions.
- Prefer `agentseek-*` distribution names and `agentseek_*` Python packages for newly created
  plugins, mainly to avoid namespace conflicts with upstream Bub and third-party packages.
- Prefer `AGENTSEEK_*` in agentseek documentation and examples, while keeping `BUB_*`
  compatibility for runtime behavior that should still work under plain Bub.
- Prefer persistent dependency wiring over ephemeral shell-only setup when the user asks to enable
  the plugin.

## Validation Checklist

Before finishing, verify:

1. Package name, Python module name, and Bub entry point are aligned.
2. New agentseek-owned packages use the `agentseek-*` / `agentseek_*` prefix unless the user
   explicitly asks for another naming contract.
3. The exported entry-point module only references modules that actually exist.
4. Dependencies in the plugin `pyproject.toml` match imported third-party packages.
5. The activation path is complete:
   either the host project depends on the package, the package is in the workspace/source mapping,
   or it was installed into the runtime environment.
6. Settings that should work in both agentseek and Bub accept both prefixes, and `BUB_*` wins when
   both values are present.
7. If the plugin uses registered Bub config, entry-point import registers it and runtime code
   accesses it consistently.
8. Tests cover the main hook or configuration path.
9. README describes the behavior and enablement path that the implementation actually provides.
10. If packaged skills were added, the build config includes `SKILL.md` and scripts.

Recommended commands to suggest, adjusted to the host project:

```bash
uv lock
uv sync
uv run pytest <plugin-tests>
uv run ruff check <changed-files>
```

For standalone local packages, also consider:

```bash
uv pip install -e /abs/path/to/plugin
```

## Agentseek Notes

When the host project is this repository:

- create new plugins under `contrib/agentseek-<feature>`
- use existing packages under `contrib/` as primary examples
- update the root `pyproject.toml` if the new package should participate in the root dev
  environment
- preserve Bub-compatible entry points under `[project.entry-points.bub]`
- mirror the existing `AGENTSEEK_*` plus `BUB_*` alias behavior used by runtime and contrib
  packages
- if a packaged agent skill is needed, follow the `src/skills/<name>/` convention used by bundled
  skills in this repo

## Output Contract

When using this skill to implement a plugin, the final response should state:

- where the plugin package was created or updated
- which Bub hooks or tools were implemented
- how the plugin was wired into the agentseek/Bub environment
- whether a packaged agent skill was added
- what tests should be run
- any remaining assumptions, especially credentials, endpoints, and runtime environment
