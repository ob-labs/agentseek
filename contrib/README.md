# Contrib

This directory contains contrib packages maintained in the `agentseek` monorepo. Each package owns the complete documentation for its install, configuration, runtime behavior, verification, and limitations.

## Purpose

Contrib packages are larger integrations that live outside the built-in `src/agentseek` documentation scope. They may have optional dependencies, backend-specific behavior, runtime entry points, or examples that should be documented next to their code.

Most contrib packages are exposed to the runtime as Bub plugins through `[project.entry-points.bub]`. In other words:

- `agentseek` names the distribution, monorepo, and user-facing packaging namespace
- `Bub` names the plugin model, hook contracts, entry-point group, and config section semantics

Contrib packages remain standard Python packages and should be added through normal dependency
management in `pyproject.toml`.

agentseek follows Bub's extension conventions. `AGENTSEEK_*` environment variables and `agentseek-*` packages belong to the agentseek distribution namespace; plugin authors should keep Bub-compatible hooks, entry points, and config behavior unless an agentseek-specific alias is needed to avoid namespace conflicts.

## Package Index

| Package | Bub entry point | Purpose |
| --- | --- | --- |
| [agentseek-tapestore-oceanbase](agentseek-tapestore-oceanbase/README.md) | `tapestore-oceanbase` | SQLAlchemy tape storage with OceanBase compatibility and optional vector retrieval. |
| [agentseek-langchain](agentseek-langchain/README.md) | `langchain` | Route Bub model execution through a LangChain `Runnable`. |
| [agentseek-schedule-sqlalchemy](agentseek-schedule-sqlalchemy/README.md) | `schedule` | Persist APScheduler jobs in a SQLAlchemy-backed store. |

## Documentation Boundary

The main `docs/` tree describes the built-in agentseek distribution layer under `src/agentseek` and `src/skills`. Contrib packages are intentionally documented here, next to their code, because they may have extra dependencies, entry points, configuration sections, examples, and backend-specific behavior.

When adding a contrib package, update its own README first. The main docs should link to it instead of duplicating its configuration reference.

## README Standard

Use this section order for package READMEs:

1. `At A Glance`: distribution name, Python package, Bub entry point, config section or surface, install path, and test target.
2. `When To Use It`: the user problem the package solves and what it does not own.
3. `Install`: root extra or workspace install, plus standalone local/Git install when supported.
4. `Configure`: environment variables, config file sections, precedence, and defaults.
5. `Run`: minimal command sequence and package-specific examples.
6. `Runtime Behavior`: hooks, lifecycle behavior, storage behavior, and fallback behavior.
7. `Verify`: Make targets and direct pytest commands.
8. `Limitations`: known boundaries and operational caveats.

Keep README facts code-backed. Check `pyproject.toml`, plugin entry points, config classes, tests, and examples before updating a package README.

Nested example READMEs can use a smaller version of the same shape: `At A Glance`, `Prerequisites`, `Configure`, `Run`, `Verify`, and `Limitations`.
