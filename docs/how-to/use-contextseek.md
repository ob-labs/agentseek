---
title: How to use ContextSeek
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli/runtime.py
  - contrib/agentseek-contextseek/README.md
---

# How to use ContextSeek

Use this when you want a semantic context layer that retrieves context
before each model turn and writes responses back after. ContextSeek is
provided by the `agentseek-contextseek` contrib package; `agentseek ctx`
forwards to its underlying `contextseek` CLI.

## Prerequisites

- `agentseek-contextseek` plugin installed:

  ```bash title="not executed in this run"
  agentseek plugin install agentseek-contextseek
  ```

  This installs the ContextSeek runtime plugin and makes the `agentseek ctx`
  forwarding commands usable in the same environment.

- ContextSeek's own backend configured. See the
  [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md).

## Steps

1. Confirm the subcommand is wired up:

   ```bash
   uv run agentseek ctx --help
   ```

   ```text title="output"
   usage: contextseek [-h]
                      {add,retrieve,expand,compact,forget,delete,overview,tools,metrics,dream,feedback,upstream,evidence-chain,chain-confidence,skill-tools,skill-context,skill-import,items}
                      ...
   ```

   The output is the upstream `contextseek` argparse help; agentseek does
   not rewrap it.

2. Add a context item:

   ```bash title="not executed in this run"
   uv run agentseek ctx add --scope my-scope --text "..."
   ```

3. Retrieve ranked hits:

   ```bash title="not executed in this run"
   uv run agentseek ctx retrieve --scope my-scope --query "..."
   ```

## Subcommand index

The forwarded `contextseek` CLI exposes (from
`agentseek ctx --help`): `add`, `retrieve`, `expand`, `compact`, `forget`,
`delete`, `overview`, `tools`, `metrics`, `dream`, `feedback`, `upstream`,
`evidence-chain`, `chain-confidence`, `skill-tools`, `skill-context`,
`skill-import`, `items`. Per-subcommand semantics live with the package
README.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek ctx` says command not found | `agentseek-contextseek` not installed | `agentseek plugin install agentseek-contextseek`. |
| `contextseek` errors about missing backend | Config not set up | See the [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md). |

## Rollback

ContextSeek storage is owned by the backend (`agentseek-contextseek` README
documents removal). To uninstall the plugin:

```bash title="not executed in this run"
uv run agentseek plugin uninstall agentseek-contextseek
```

## Related

- Contrib: [agentseek-contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
- Reference: [CLI reference](../reference/cli.md), [Packages reference](../reference/packages.md)
