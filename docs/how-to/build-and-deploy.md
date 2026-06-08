---
title: How to build and deploy
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/lifecycle/commands/build.py
  - src/agentseek/lifecycle/commands/deploy.py
  - Dockerfile
---

# How to build and deploy

Use this when you have a generated project and want a container image plus
Compose / Kubernetes manifests.

## Prerequisites

- `agentseek` installed in the project environment.
- `docker` and optionally `docker buildx`.
- For `deploy`, `--dry-run` is required in the current implementation.

## Build

```bash title="not executed in this run"
uv run agentseek build --tag my-agent:0.1.0
```

Dry-run the resolved Docker command:

```bash title="not executed in this run"
uv run agentseek build --dry-run --tag my-agent:0.1.0
```

Common flags:

| Flag | Default | Description |
| --- | --- | --- |
| `--tag`, `-t` | `<cwd-slug>:latest` | Image tag. |
| `--file`, `-f` | `Dockerfile` | Dockerfile path. |
| `--context` | `.` | Build context directory. |
| `--platform` | - | Comma-separated targets. |
| `--push` | off | Push after build. |
| `--no-cache` | off | Skip cache. |
| `--build-arg KEY=VALUE` | - | Repeatable build-time variable. |
| `--dry-run` | off | Print without executing. |

## Deploy manifests

```bash title="not executed in this run"
uv run agentseek deploy --dry-run --image my-agent:0.1.0
```

Common flags:

| Flag | Default | Description |
| --- | --- | --- |
| `--dry-run` | required | Generate manifests without applying them. |
| `--mode` | `both` | `docker-compose`, `k8s`, or `both`. |
| `--output` | `deploy` | Output directory. |
| `--image` | `<project-slug>:latest` | Container image reference. |
| `--slug` | inferred | Service / deployment name stem. |
| `--port` | `8000` | Service port. |
| `--replicas` | `1` | Kubernetes replicas. |
| `--namespace` | `default` | Kubernetes namespace. |

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek build` not found | Project environment is not synced | Run `uv sync`, then retry with `uv run agentseek build`. |
| `--push` fails with `unauthorized` | Registry login missing | Run `docker login <registry>`. |
| `agentseek deploy` errors without `--dry-run` | Current deploy command only writes manifests | Add `--dry-run`. |
| Manifest references the wrong image | `--image` not set | Pass `--image my-agent:0.1.0`. |

## Related

- [CLI reference](../reference/cli.md)
- [Docker reference](../reference/docker.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
