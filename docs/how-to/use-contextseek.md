---
title: How to use ContextSeek
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - contrib/agentseek-contextseek/README.md
---

# How to use ContextSeek

Use this when you want AgentSeek to use ContextSeek memory.

## Prerequisites

- AgentSeek is installed in the current project.
- You know where ContextSeek should store project data.

## Steps

1. Add ContextSeek to the project.

   ```bash
   uv add agentseek-contextseek
   ```

2. Configure ContextSeek storage.

   ```bash title=".env"
   AGENTSEEK_CTX_STORAGE_PATH=.contextseek/store
   ```

3. Check the forwarded CLI.

   ```bash
   uv run agentseek ctx --help
   ```

   ```text title="output"
   usage: contextseek [-h]
                      {add,retrieve,expand,compact,forget,delete,overview,tools,metrics,dream,feedback,upstream,evidence-chain,chain-confidence,skill-tools,skill-context,skill-import,items}
                      ...
   ```

4. Add a context item.

   ```bash
   uv run agentseek ctx add --scope my-scope --text "..."
   ```

5. Retrieve ranked hits.

   ```bash
   uv run agentseek ctx retrieve --scope my-scope --query "..."
   ```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek ctx` asks for `agentseek-contextseek` | The package is not installed in this project. | Run `uv add agentseek-contextseek`. |
| ContextSeek reports missing backend config | Storage or backend settings are missing. | Add the required `AGENTSEEK_CTX_*` values. |

## Rollback

Remove the package and the storage directory you configured.

```bash
uv remove agentseek-contextseek
rm -rf .contextseek/store
```

## Related

- Contrib: [agentseek-contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
- Reference: [CLI reference](../reference/cli.md), [Packages reference](../reference/packages.md)
