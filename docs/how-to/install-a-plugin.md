---
title: How to install a plugin
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/env.py
---

# How to install a plugin

Use this when you need to add a new Bub-compatible plugin (channel, model
provider, store, tool package, scheduler, …) to an agentseek workspace.
Plugins install into the **plugin sandbox**, a uv-managed project at
`AGENTSEEK_PROJECT` / `BUB_PROJECT`.

## Prerequisites

- agentseek installed and on `PATH` as `uv run agentseek`.
- Network access — `agentseek install` resolves git URLs and the Bub contrib
  registry.

## Steps

1. Pick a plugin spec. `agentseek install` accepts (`reference/cli.md#agentseek-install-specs`):

   - a git URL
   - `owner/repo`
   - a package name in `bub-contrib` (often `name@branch`)

   It is **not** a generic PyPI installer for arbitrary distribution names.

2. (Optional) Pin the sandbox location. The default is
   `${BUB_HOME}/agentseek-project` (`src/agentseek/env.py:72`). To keep
   plugins out of your repo, set:

   ```bash title=".env"
   AGENTSEEK_PROJECT=/home/me/.config/agentseek/plugin-sandbox
   ```

3. Install the plugin. The first call initialises the sandbox via
   `uv init --bare --name agentseek-project --app` and adds the Bub
   requirement (`src/agentseek/cli.py:134`).

   ```bash title="not executed in this run"
   uv run agentseek install bub-feishu@main
   ```

4. Verify the sandbox now lists the plugin:

   ```bash title="not executed in this run"
   cat "${BUB_PROJECT:-.agentseek/agentseek-project}/pyproject.toml"
   ```

### CLI shortcut

The library form **is** the CLI form for installs. There is no embedding API;
`agentseek install` shells out to `uv` inside the sandbox.

`bub install <spec>` from upstream Bub works equivalently. The agentseek CLI
only adds the sandbox default and branding.

## Removing a plugin

```bash title="not executed in this run"
uv run agentseek uninstall <package-name>
```

`PACKAGES` are the distribution names listed in the sandbox `pyproject.toml`.

## Updating plugins

```bash title="not executed in this run"
uv run agentseek update              # update all
uv run agentseek update bub-feishu   # update one
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` on first install | Sandbox path missing | agentseek's `_ensure_plugin_sandbox` (`src/agentseek/cli.py:123`) creates it; if you see this, file a bug. |
| Plugin loads but not picked up by runtime | Plugin is in the sandbox but the runtime is reading a different `BUB_PROJECT` | Confirm `${BUB_PROJECT}` matches the path you installed into. |

## Rollback

`uv run agentseek uninstall <name>` removes the package from the sandbox. To
discard the entire sandbox, delete `${AGENTSEEK_PROJECT}` (default
`.agentseek/agentseek-project`). The next install rebuilds it.

## Related

- How-to: `author-a-contrib-plugin.md`, `add-skills.md`
- Reference: `../reference/cli.md`, `../reference/file-layout.md`
- Concepts: `../explanation/extension-model.md`
