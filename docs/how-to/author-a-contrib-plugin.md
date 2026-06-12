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

Use this when you want to add a Bub-compatible plugin under
`contrib/agentseek-<feature>/`.

## Prerequisites

- Read the [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md).
- Decide which Bub hook or entry point your plugin registers.

## Steps

1. Create `contrib/agentseek-<feature>/`.

2. Add it to the root workspace.

   ```toml title="pyproject.toml"
   [tool.uv.workspace]
   members = [
     # ... existing members
     "contrib/agentseek-<feature>",
     ".agentseek/agentseek-project",
   ]
   ```

3. Use the standard names.

   | Item | Convention |
   | --- | --- |
   | Distribution name | `agentseek-<feature>` |
   | Python package | `agentseek_<feature>` |
   | Bub entry point group | `[project.entry-points.bub]` |
   | Env vars | prefer `AGENTSEEK_*`; accept `BUB_*` for Bub runtime settings |

4. Write the package README with these sections.

   1. `At A Glance`
   2. `When To Use It`
   3. `Install`
   4. `Configure`
   5. `Run`
   6. `Runtime Behavior`
   7. `Verify`
   8. `Limitations`

5. Expose the package as an optional dependency when users should install it
   from the root project.

   ```toml title="pyproject.toml"
   [project.optional-dependencies]
   <feature> = ["agentseek-<feature>"]
   ```

6. Pin the workspace source.

   ```toml
   agentseek-<feature> = { workspace = true }
   ```

### CLI shortcut

There is no `agentseek plugin new` command. Use the `plugin-creator` skill, or
copy an existing `contrib/agentseek-*/` package and rename it.

## Boundaries

- Keep package-specific docs in the package README.
- Link from `docs/` instead of copying contrib README content.

## Related

- Contrib standard: [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
- How-to: [How to install a plugin](install-a-plugin.md), [How to add skills](add-skills.md)
- Reference: [Packages reference](../reference/packages.md)
- Concepts: [The extension model](../explanation/extension-model.md)
