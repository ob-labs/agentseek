---
title: How to build and deploy
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/commands/build.py
  - src/agentseek/cli/commands/deploy.py
  - Dockerfile
---

# How to build and deploy

Use this when you have a generated project and need deployable artifacts.

## Prerequisites

- Run commands from a generated project root.
- The project has a `Dockerfile`.
- Docker is installed.

## Build the image

```bash
uv run agentseek build --tag my-agent:0.1.0
```

Preview the Docker command first when you want to check paths or tags:

```bash
uv run agentseek build --dry-run --tag my-agent:0.1.0
```

Push after a successful build when your registry login is ready:

```bash
uv run agentseek build --tag registry.example.com/my-agent:0.1.0 --push
```

## Generate manifests

```bash
uv run agentseek deploy --dry-run --image my-agent:0.1.0
```

```text title="output"
wrote deploy/docker-compose.yaml
wrote deploy/k8s/deployment.yaml
wrote deploy/k8s/service.yaml
agentseek deploy --dry-run --mode both → 3 file(s) under deploy (image=my-agent:0.1.0, slug=my-bub-agent).
```

Choose one target when you do not need both Compose and Kubernetes:

```bash
uv run agentseek deploy --dry-run --mode k8s --image my-agent:0.1.0
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek build` is unavailable | The command is not running from a generated project root. | Enter the project created by `agentseek create` and run `uv sync` first. |
| `--push` fails with `unauthorized` | Registry login is missing. | Run `docker login <registry>`. |
| `deploy` rejects the command | `--dry-run` is required. | Add `--dry-run`. |
| Manifest references the wrong image | `--image` was omitted. | Pass the image explicitly. |

## Rollback

Remove the generated `deploy/` directory when you do not want the manifests.

## Related

- [CLI reference](../reference/cli.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
