---
title: CLI reference
type: reference
audience: [A1, A2, A3, A4]
runs: yes
verified_on: 2026-06-08
sources:
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/surface.py
  - src/agentseek/cli/commands/
---

# CLI reference

## Usage

```bash
agentseek [OPTIONS] COMMAND [ARGS]...
```

Commands are grouped by area:

| Area | Commands | Purpose |
| --- | --- | --- |
| Project | `create`, `run`, `build`, `deploy` | Create, run, build, and package projects. |
| Runtime | `chat`, `turn`, `gateway` | Interact with the harness. |
| Environment | `plugin`, `mcp`, `onboard`, `login` | Manage runtime configuration and plugins. |
| Services | `api`, `ctx`, `skills` | Bridge optional AgentSeek services and skill tooling. |

## Project management

### `agentseek create [SPEC]`

Create a new project from a bundled or external template.

| Argument / flag | Type | Default | Description |
| --- | --- | --- | --- |
| `spec` | TEXT | - | Template family, `family/name`, git URL, or local path. |
| `--template` | TEXT | - | Named template inside the selected family. |
| `--checkout` | TEXT | - | Branch, tag, or commit for remote templates. |
| `--list-templates` | flag | off | List available templates and exit. |
| `--no-input` | flag | off | Skip interactive Cookiecutter prompts. |

See [Templates reference](templates.md) for the bundled template catalogue.

### `agentseek run`

Run a generated project locally.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--port` | INTEGER | `$PORT` or `3000` | Frontend port. |
| `--host` | TEXT | `127.0.0.1` | Host used for readiness probes. |
| `--no-browser` | flag | off | Do not open a browser. |
| `--wait-timeout` | INTEGER | `30` | Seconds to wait for readiness. |
| `--mode` | `auto\|compose\|python` | `auto` | Launch mode override. |

### `agentseek build`

Build the current project into a container image.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--tag`, `-t` | TEXT | `<cwd-slug>:latest` | Image tag. |
| `--file`, `-f` | PATH | `Dockerfile` | Dockerfile path. |
| `--context` | PATH | `.` | Build context. |
| `--platform` | TEXT | - | Comma-separated target platforms. |
| `--push` | flag | off | Push after a successful build. |
| `--no-cache` | flag | off | Disable build cache. |
| `--build-arg` | TEXT | repeatable | Build-time `KEY=VALUE` variables. |
| `--dry-run` | flag | off | Print the resolved Docker command. |

### `agentseek deploy`

Generate deployment manifests. In the current implementation `--dry-run` is
required, so the command writes files but does not apply them.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--dry-run` | flag | required | Generate manifests without deploying. |
| `--mode` | `docker-compose\|k8s\|both` | `both` | Manifest target. |
| `--output` | DIRECTORY | `deploy` | Output directory. |
| `--image` | TEXT | `<project-slug>:latest` | Container image reference. |
| `--slug` | TEXT | inferred | Service or deployment name stem. |
| `--port` | INTEGER | `8000` | Service port. |
| `--replicas` | INTEGER | `1` | Kubernetes replica count. |
| `--namespace` | TEXT | `default` | Kubernetes namespace. |

## Runtime

### `agentseek chat`

Start an interactive CLI chat session with MCP and skill support.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--chat-id` | TEXT | `local` | Chat id. |
| `--session-id` | TEXT | `None` | Optional session id. |

### `agentseek turn MESSAGE`

Run one inbound message through the runtime.

| Argument / flag | Type | Default | Description |
| --- | --- | --- | --- |
| `MESSAGE` | TEXT | - | User message. |
| `--channel` | TEXT | `cli` | Inbound channel name. |
| `--chat-id` | TEXT | `local` | Chat id. |
| `--sender-id` | TEXT | `user` | Sender id. |
| `--session-id` | TEXT | `None` | Optional session id. |

### `agentseek gateway`

Start message listeners for configured channels.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--enable-channel` | TEXT | all | Channel to enable; repeatable. |

## Environment

### `agentseek plugin install [SPECS]...`

Install runtime plugins into the AgentSeek plugin sandbox (default:
`.agentseek/agentseek-project`).

### `agentseek plugin uninstall PACKAGES...`

Remove packages from the plugin sandbox.

### `agentseek plugin update [PACKAGES]...`

Update selected plugin packages, or the sandbox when no package is given.

### `agentseek onboard`

Run the interactive configuration flow and write runtime config.

### `agentseek mcp`

Manage MCP server configuration.

### `agentseek login`

Run the configured authentication flow when the installed runtime exposes it.

## Services

### `agentseek api`

Forward service commands to `agentseek-api` when that package is installed.
Available subcommands are `dev`, `serve`, `dockerfile`, `build`, `up`, and
`version`.

### `agentseek ctx`

Forward ContextSeek commands when the ContextSeek CLI is installed. Common
subcommands include `add`, `retrieve`, `expand`, `compact`, `forget`,
`delete`, `overview`, `tools`, `metrics`, and skill import helpers.

### `agentseek skills`

Manage skills through `npx-skills` when available, falling back to `npx`.

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--dir` | PATH | `$PWD` | Workspace directory. |

Subcommands: `add`, `list`, `find`, `update`, `remove`, `init`.

## Verification

Useful smoke checks:

```bash
uv run agentseek --help
uv run agentseek create --help
uv run agentseek chat --help
uv run agentseek turn --help
uv run agentseek plugin --help
```
