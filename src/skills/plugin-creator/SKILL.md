---
name: plugin-creator
description: |
 Create or update an agentseek/Bub plugin in any local path. Use when the task is to scaffold a
 Python package that exposes a [project.entry-points.bub] entry, implements Bub hooks or tools,
 and is installed or wired as a dependency in the agentseek runtime project. Prefer agentseek's
 package and environment naming conventions while preserving Bub compatibility.
---

# Agentseek Plugin Creator

Create agentseek plugins as normal Python packages that follow Bub's extension model.

Core rule: a plugin becomes effective only when both conditions are true:

1. the package exposes an entry point in the `bub` group
2. the package is installed in the same Python environment as agentseek/Bub

Agentseek is a distribution and runtime layer on top of Bub, not a separate plugin system. Keep
Bub hooks, tool decorators, and entry-point groups compatible unless there is a clear agentseek-only
reason to do otherwise.

## What Counts As A Plugin

A plugin is usually a Python package with:

- `pyproject.toml`
- `README.md`
- `src/<python_package>/__init__.py`
- `src/<python_package>/plugin.py` or another hook-exporting module such as `tools.py`
- optional helper modules such as `channel.py`, `store.py`, `job_store.py`, or `settings.py`
- optional tests under `tests/` or `src/tests/`, matching the host repository's convention
- optional bundled agent skill files under `src/skills/<skill-name>/`

The package must export a Bub entry point:

```toml
[project.entry-points.bub]
<plugin-name> = "<python_package>.plugin"
```

Other valid targets also exist:

```toml
[project.entry-points.bub]
<plugin-name> = "<python_package>.tools"
<plugin-name> = "<python_package>.plugin:main"
```

Use the narrowest export surface that matches the implementation.

## First: Identify The Host Project

Before creating files, determine where the plugin should live and where agentseek/Bub runs.

Common cases:

1. Existing agentseek monorepo package
   Create or update a package under `contrib/` and wire it into the root dependency flow.

2. Standalone local package
   Create a new package in the requested local path, then install it into the agentseek/Bub
   environment with an editable or path-based dependency.

3. Existing package to extend
   Update the package in place and make sure the environment uses the updated dependency.

Important distinction:

- plugin source location: where files are created
- activation location: the project or environment that installs the package

If the task is ambiguous, infer both from nearby files such as `pyproject.toml`, `uv.lock`,
`.venv`, and how `agentseek` or `bub` is launched.

## Classify The Plugin Shape

Inspect the closest existing plugin before writing code. In this repository, prefer packages under
`contrib/` as the primary examples.

Common shapes:

1. Channel provider
   Use when the plugin connects agentseek/Bub to an external message source or sink.
   Typical hook: `provide_channels`.

2. Hook-only provider
   Use when the plugin contributes one focused hook such as model execution.
   Typical hook: `run_model`.

3. Resource provider
   Use when the plugin returns a store or singleton runtime resource.
   Typical hook: `provide_tape_store`.

4. Composite plugin
   Use when the plugin owns runtime state and also provides channels or tools.
   Typical hooks: `load_state` plus one or more provider hooks.

5. Tool registration package
   Use when the package mainly exposes `@tool` functions and exports the tool module directly.

Prefer copying the nearest existing shape over inventing a new abstraction.

## Naming And Compatibility

For agentseek-owned plugins, prefer:

- distribution name: `agentseek-<feature>`
- Python package: `agentseek_<feature>`
- Bub entry point name: a short user-facing name, for example `schedule`
- entry point group: always `bub`

For upstream Bub plugins or packages intended to live outside agentseek, `bub-<feature>` and
`bub_<feature>` are still valid. Do not rename third-party packages unless the user explicitly asks.

Environment variables should follow this rule:

- prefer `AGENTSEEK_*` in agentseek documentation and examples
- accept `BUB_*` for Bub compatibility when the setting is part of the Bub runtime contract
- if both prefixes are present for the same setting, prefer `BUB_*`
- use `pydantic-settings` `AliasChoices` for package-local settings when practical
- preserve stable external names for shipped behavior, persisted data, and public interfaces

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
- include scripts under `src/skills/<skill-name>/scripts/` when scripts are needed
- make sure packaging includes `SKILL.md` and scripts

### 6. Wire The Plugin Into The Runtime

This step is mandatory. Creating the package alone does not activate it.

Pick one activation path:

1. Add as a normal dependency in the agentseek host project.
2. Add as a workspace package and source mapping.
3. Install directly into the active environment with `uv pip install -e /abs/path/to/plugin`.

When the task says "make it effective", prefer option 1 or 2 over a one-off install unless the user
clearly wants a local experiment.

### 7. Write The Minimum Useful README

Keep the README short and operational. Usually include:

- what the plugin provides
- required environment variables or configuration
- how to install or enable it
- any notable behavior or limitations

Do not pad it with generic packaging tutorials.

### 8. Add Targeted Tests

Non-trivial plugin behavior should have tests.

Favor narrow tests over large integration scaffolding. Typical coverage:

- entry hook returns the right type or object
- settings parse environment variables correctly
- plugin-level singleton or factory behavior
- fallback and error-path behavior for boundary conditions

Use the host project's test style.

## Validation Checklist

Before finishing, verify:

1. Package name, Python module name, and Bub entry point are aligned.
2. The exported entry-point module only references modules that actually exist.
3. Dependencies in the plugin `pyproject.toml` match imported third-party packages.
4. The activation path is complete: the host project depends on the package, the package is in the
   workspace/source mapping, or it was installed into the runtime environment.
5. Tests cover the main hook or configuration path.
6. README describes the behavior and enablement path that the implementation actually provides.
7. If packaged skills were added, the build config includes `SKILL.md` and scripts.

Recommended commands, adjusted to the host project:

```bash
uv lock
uv run pytest <plugin-tests>
uv run ruff check <changed-files>
```

## Output Contract

When using this skill to implement a plugin, the final response should state:

- where the plugin package was created or updated
- which Bub hooks or tools were implemented
- how the plugin was wired into the agentseek/Bub environment
- whether a packaged agent skill was added
- what validation was run
- any remaining assumptions, especially credentials, endpoints, and runtime environment
