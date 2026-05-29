---
title: How to add skills
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - pyproject.toml
  - entrypoint.sh
---

# How to add skills

Use this when the extension is **instruction or workflow knowledge** — a
`SKILL.md` file plus optional scripts — rather than a new runtime hook. Use
`install-a-plugin.md` instead when you need a new channel, store, or tool
registration.

## Pick a scope

| Scope | Path | When |
| --- | --- | --- |
| Project-local | `.agents/skills/<name>/SKILL.md` | Repository-specific behaviour. Do not ship with the package. |
| Bundled (release) | `src/skills/<name>/SKILL.md` | Behaviour that should exist wherever `agentseek` is installed. Goes into the wheel via `pyproject.toml:74`. |
| External (build-imported) | `[tool.pdm.build].skills` in `pyproject.toml:78` | Pull selected skills from another repo at build time. |

Bub discovers project-local skills from `.agents/skills/`. The Docker
entrypoint preserves this convention by default and symlinks alternate
locations into the same path (`entrypoint.sh:30`–`:35`).

## Steps — install a project-local skill

1. Add the skill directory and minimal `SKILL.md`:

   ```bash
   mkdir -p .agents/skills/my-skill
   ```

   ```markdown title=".agents/skills/my-skill/SKILL.md"
   # my-skill

   When to use: <describe trigger>.
   Steps:
   1. ...
   ```

2. The skill is picked up on the next `agentseek chat` / `agentseek
   gateway`. No restart of any sandbox is required.

### CLI shortcut — install from a registry

`agentseek skills` wraps the upstream `vercel-labs/skills` CLI (run via
`npx`). Subcommands: `add`, `list`, `find`, `update`, `remove`, `init`.

```bash title="not executed in this run"
uv run agentseek skills --dir . add psiace/skills --skill friendly-python
```

## Steps — bundle a release skill

1. Place the skill under `src/skills/<name>/SKILL.md`. `pyproject.toml:74`
   already includes `src/skills` in the wheel.

2. Build the wheel and confirm the skill shows up:

   ```bash title="not executed in this run"
   uv build
   ```

3. The skill is then available wherever `agentseek` is installed.

## Steps — import an external skill at build time

Edit `[tool.pdm.build].skills` in `pyproject.toml:78` to point at the source
repository, subpath, and the skill subset you want:

```toml title="pyproject.toml"
[tool.pdm.build]
skills = [
  { git = "https://github.com/PsiACE/skills.git", subpath = "skills", include = ["friendly-python", "piglet"] },
]
```

The `pdm-build-skills` backend resolves these at build time.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Skill never invoked | `SKILL.md` trigger description does not match the task | Tighten the "When to use" line. |
| Skill in `src/skills/` not visible after install | You installed from source without rebuilding | `uv sync` or `uv build` again. |
| Container ignores host skills | `AGENTSEEK_SKILLS_HOME` is set to a non-default path and Bub is scanning the link | Confirm symlink exists at `${workspace}/.agents/skills` (`entrypoint.sh:33`). |

## Rollback

Delete the skill directory under `.agents/skills/` or `src/skills/`. Rebuild
if you bundled it.

## Related

- How-to: `install-a-plugin.md`, `author-a-contrib-plugin.md`
- Reference: `../reference/packages.md`, `../reference/file-layout.md`
- Project conventions: [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md)
