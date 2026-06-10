---
title: How to author a contrib plugin
type: how-to
audience: [A3]
runs: no
verified_on: 2026-05-28
sources:
  - contrib/README.md
  - pyproject.toml
---

# How to author a contrib plugin

Use this when you need a Bub-compatible plugin that lives in this monorepo
as `contrib/agentseek-<feature>/`. The plugin contract, README shape, and
distribution conventions are owned by the [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) — this page
points you at it and lists the agentseek-specific bits you must not skip.

## Prerequisites

- Read the [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) first. That is the source of truth for the
  README standard.
- Decide which Bub entry point group your plugin belongs to (`[project.entry-points.bub]`).

## Steps

1. Create a workspace member at `contrib/agentseek-<feature>/` and add it
   to the workspace list in `pyproject.toml:101`:

   ```toml title="pyproject.toml"
   [tool.uv.workspace]
   members = [
     # ... existing members
     "contrib/agentseek-<feature>",
     ".agentseek/agentseek-project",
   ]
   ```

2. Follow the contrib **naming conventions**
   ([contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md), "agentseek follows Bub's extension conventions"):

   | Item | Convention |
   | --- | --- |
   | Distribution name | `agentseek-<feature>` |
   | Python package | `agentseek_<feature>` |
   | Bub entry point group | `[project.entry-points.bub]` |
   | Env vars | prefer `AGENTSEEK_*`; accept `BUB_*` for Bub runtime settings |
   | When both prefixes exist | `BUB_*` wins (matches `apply_agentseek_env_aliases`, `src/agentseek/env.py:63`) |

3. Write the README using the section order from the
   [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) ("README Standard"):

   1. `At A Glance`
   2. `When To Use It`
   3. `Install`
   4. `Configure`
   5. `Run`
   6. `Runtime Behavior`
   7. `Verify`
   8. `Limitations`

4. (Optional) Expose the package as an extra in the root
   `pyproject.toml:27`:

   ```toml title="pyproject.toml"
   [project.optional-dependencies]
   <feature> = ["agentseek-<feature>"]
   ```

   And pin the workspace source in `[tool.uv.sources]`
   (`pyproject.toml:87`):

   ```toml
   agentseek-<feature> = { workspace = true }
   ```

5. Use the bundled `plugin-creator` skill to scaffold the package. The
   agentseek-adapted version mirrors the upstream Bub contrib workflow but
   specializes for `contrib/agentseek-*`, `AGENTSEEK_*` aliases, and bundled
   `src/skills` (see [The extension model](../explanation/extension-model.md)).

### CLI shortcut

There is no `agentseek plugin new` command. Use the `plugin-creator` skill
inside a chat session, or copy an existing `contrib/agentseek-*/` and
rename.

## Boundaries

- Do **not** duplicate the per-package README into `docs/`. Cross-link
  to it instead.
- The main `docs/` tree documents only `src/agentseek` and `src/skills`
  ([contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md), "Documentation Boundary").

## Related

- Contrib standard: [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
- How-to: [How to install a plugin](install-a-plugin.md), [How to add skills](add-skills.md)
- Reference: [Packages reference](../reference/packages.md)
- Concepts: [The extension model](../explanation/extension-model.md)
