---
title: How to build and deploy
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - contrib/agentseek-cli/README.md
  - contrib/agentseek-cli/pyproject.toml
  - Dockerfile
---

# How to build and deploy

Use this when you have a generated project (see
[Templates reference](../reference/templates.md)) and want to ship it as a container image and a
set of Compose / Kubernetes manifests. Both commands are provided by
`agentseek-cli` (`pyproject.toml:31`).

## Prerequisites

- `agentseek[cli]` installed (or the `agentseek-cli` workspace member active).
- `docker` (and optionally `docker buildx`) for `build`.
- For `deploy`: nothing at runtime — `--dry-run` is required in v1, so the
  command only writes manifests.

## Build a container image

1. From the project root, build:

   ```bash title="not executed in this run"
   uv run agentseek build --tag my-agent:0.1.0
   ```

2. Flags (from `agentseek build --help`):

   | Flag | Default | Description |
   | --- | --- | --- |
   | `--tag`, `-t` | `<cwd-slug>:latest` | Image tag. |
   | `--file`, `-f` | resolved by `agentseek-cli` | Dockerfile path. |
   | `--context` | `.` | Build context directory. |
   | `--platform` | — | Comma-separated targets, e.g. `linux/amd64,linux/arm64`. |
   | `--push` | off | Push after build (requires registry login). |
   | `--no-cache` | off | Skip cache. |
   | `--build-arg KEY=VALUE` | — | Repeatable build-time variable. |
   | `--dry-run` | off | Print the resolved command(s) without executing. |

3. Print what would happen, without building:

   ```bash title="not executed in this run"
   uv run agentseek build --dry-run --tag my-agent:0.1.0
   ```

## Generate deployment manifests

In v1, `--dry-run` is **required** — the command only writes manifests, it
does not deploy.

1. Generate both docker-compose and k8s manifests under `deploy/`:

   ```bash title="not executed in this run"
   uv run agentseek deploy --dry-run --image my-agent:0.1.0
   ```

2. Flags (from `agentseek deploy --help`):

   | Flag | Default | Description |
   | --- | --- | --- |
   | `--dry-run` | required | Generate manifests without deploying. |
   | `--mode` | `both` | `docker-compose`, `k8s`, or `both`. |
   | `--output` | `deploy` | Directory to write manifests into. |
   | `--image` | `<project-slug>:latest` | Container image reference. |
   | `--slug` | inferred from cwd | Project slug used in service / deployment names. |
   | `--port` | `8000` | Service port. |
   | `--replicas` | `1` | k8s Deployment replicas (must be ≥ 1). |
   | `--namespace` | `default` | k8s namespace. |

### Scope

These commands belong to `agentseek-cli`, the **project lifecycle CLI**. There
is no separate harness-runtime equivalent; use Path A directly, or run them
from a merged environment where `agentseek-cli` is installed alongside the
harness. See the
[agentseek-cli README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek build` not found | `agentseek[cli]` not installed | `uv sync --extra cli` or add `agentseek-cli` to your project. |
| `--push` fails with `unauthorized` | Registry login missing | `docker login <registry>` first. |
| `agentseek deploy` errors without `--dry-run` | v1 hard-requires `--dry-run` | Add the flag. |
| Manifest references the wrong image | `--image` not set; slug fallback used | Pass `--image my-agent:0.1.0`. |

## Rollback

`agentseek build` does not delete its outputs. To remove a built image:

```bash title="not executed in this run"
docker image rm my-agent:0.1.0
```

`agentseek deploy --dry-run` only writes files; delete the `deploy/`
directory if you want to discard them.

## Related

- How-to: [How to run with Docker Compose](run-with-docker-compose.md)
- Reference: [CLI reference](../reference/cli.md), [Docker reference](../reference/docker.md)
- Contrib: [agentseek-cli README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md)
