---
title: How to install a plugin
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/plugin.py
  - src/agentseek/env.py
---

# How to install a plugin

Use this when you want to add a Bub-compatible plugin to an AgentSeek workspace.

## Prerequisites

- AgentSeek is available as `agentseek`.
- Network access for git URLs or the Bub contrib registry.

## Steps

1. Choose a plugin spec.

   ```text
   bub-feishu@main
   ob-labs/agentseek
   https://github.com/example/plugin.git
   agentseek-contextseek
   ```

2. Pin the plugin sandbox when you do not want it under the workspace.

   ```bash title=".env"
   AGENTSEEK_PROJECT=/home/me/.config/agentseek/plugin-sandbox
   ```

3. Install the plugin.

   ```bash
   agentseek plugin install bub-feishu@main
   ```

4. Check the sandbox package file.

   ```bash
   cat "${BUB_PROJECT:-${AGENTSEEK_PROJECT:-.agentseek/agentseek-project}}/pyproject.toml"
   ```

## Removing a plugin

```bash
agentseek plugin uninstall <package-name>
```

`PACKAGES` are the distribution names listed in the sandbox `pyproject.toml`.

## Updating a plugin

```bash
agentseek plugin update              # update all
agentseek plugin update bub-feishu   # update one
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Plugin installs into the wrong place | Another project path is set. | Check `AGENTSEEK_PROJECT` and `BUB_PROJECT`. |
| Plugin is installed but not loaded | Runtime reads another sandbox. | Start the runtime with the same project path. |

## Rollback

Uninstall the package, or delete `${AGENTSEEK_PROJECT}` to discard the whole
sandbox. The next install recreates it.

## Related

- How-to: [How to author a contrib plugin](author-a-contrib-plugin.md), [How to add skills](add-skills.md)
- Reference: [CLI reference](../reference/cli.md), [File layout reference](../reference/file-layout.md)
- Concepts: [The extension model](../explanation/extension-model.md)
