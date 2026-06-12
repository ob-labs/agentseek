---
title: How to add skills
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - pyproject.toml
  - entrypoint.sh
---

# How to add skills

Use this when you want to add instruction or workflow knowledge with a
`SKILL.md` file.

## Add a project skill

1. Create the skill directory.

   ```bash
   mkdir -p .agents/skills/my-skill
   ```

2. Add the skill instructions.

   ```markdown title=".agents/skills/my-skill/SKILL.md"
   # my-skill

   When to use: <describe trigger>.
   Steps:
   1. ...
   ```

3. Start a new runtime process.

   ```bash
   uv run agentseek chat
   ```

Use `.agents/skills/<name>/` for project-local skills. Use
`src/skills/<name>/` only for skills that should ship with the package.

### CLI shortcut

Install from a registry when the skill already lives elsewhere:

```bash
agentseek skills add --all --global
agentseek skills add --skill langsmith-trace --global --yes
agentseek skills add langchain-ai/langsmith-skills --skill '*' --yes
```

## Bundle a release skill

Place the skill under `src/skills/<name>/SKILL.md`, then build the package.

```bash
uv build
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Skill never runs | The trigger is too vague. | Tighten the "When to use" line. |
| Release skill is missing | The package was not rebuilt. | Run `uv build` again. |
| Container misses host skills | The container points at another skills path. | Set `AGENTSEEK_SKILLS_HOME=/workspace/.agents/skills`. |

## Rollback

Delete the skill directory. Rebuild the package if you removed a bundled skill.

## Related

- How-to: [How to install a plugin](install-a-plugin.md), [How to author a contrib plugin](author-a-contrib-plugin.md)
- Reference: [Packages reference](../reference/packages.md), [File layout reference](../reference/file-layout.md)
- Project conventions: [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md)
