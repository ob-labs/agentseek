---
title: CLI reference
type: reference
audience: [A1, A2, A3, A4]
runs: no
verified_on: 2026-06-12
sources:
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/__init__.py
  - src/agentseek/cli/commands/
---

# CLI reference

```text
agentseek [OPTIONS] COMMAND [ARGS]...
```

## Command groups

| Area | Commands |
| --- | --- |
| Project | `create`, `run`, `build`, `deploy` |
| Runtime | `chat`, `turn`, `gateway` |
| Environment | `plugin`, `onboard`, `login`, optional `mcp` |
| Services | `api`, `ctx`, `skills` |
| Utility | `version` |

## Project commands

### `agentseek create [SPEC]`

| Argument / flag | Type | Default | Description |
| --- | --- | --- | --- |
| `spec` | text | - | Framework type, `type/name`, git URL, or local path. |
| `--template` | text | - | Named template under the selected type; no value lists templates. |
| `--checkout` | text | - | Branch, tag, or commit for a remote template. |
| `--list-templates` | flag | off | List templates and exit. |
| `--no-input` | flag | off | Use template defaults without prompts. |

### `agentseek run`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--port` | integer | `$PORT` or `3000` | Frontend port. |
| `--host` | text | `127.0.0.1` | Readiness probe host. |
| `--no-browser` | flag | off | Skip opening the default browser. |
| `--wait-timeout` | integer | `30` | Seconds to wait for frontend readiness. |
| `--mode` | `auto`, `compose`, `python` | `auto` | Launch mode. |

### `agentseek build`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--tag`, `-t` | text | `<cwd-slug>:latest` | Image tag. |
| `--file`, `-f` | path | `Dockerfile` | Dockerfile path. |
| `--context` | path | `.` | Build context. |
| `--platform` | text | - | Comma-separated target platforms. |
| `--push` | flag | off | Push after a successful build. |
| `--no-cache` | flag | off | Disable build cache. |
| `--build-arg` | text | repeatable | Build-time `KEY=VALUE` variable. |
| `--dry-run` | flag | off | Print resolved Docker command without executing it. |

### `agentseek deploy`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--dry-run` | flag | required | Generate manifest files without applying them. |
| `--mode` | `docker-compose`, `k8s`, `both` | `both` | Manifest target. |
| `--output` | directory | `deploy` | Output directory. |
| `--image` | text | `<project-slug>:latest` | Container image reference. |
| `--slug` | text | inferred from cwd | Service or deployment name stem. |
| `--port` | integer | `8000` | Service port. |
| `--replicas` | integer | `1` | Kubernetes replica count. |
| `--namespace` | text | `default` | Kubernetes namespace. |

## Runtime commands

### `agentseek chat`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--chat-id` | text | `local` | Chat id. |
| `--session-id` | text | - | Optional session id. |

### `agentseek turn MESSAGE`

| Argument / flag | Type | Default | Description |
| --- | --- | --- | --- |
| `MESSAGE` | text | required | Inbound message content. |
| `--channel` | text | `cli` | Message channel. |
| `--chat-id` | text | `local` | Chat id. |
| `--sender-id` | text | `human` | Sender id. |
| `--session-id` | text | - | Optional session id. |

### `agentseek gateway`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--enable-channel` | text | all | Channel to enable; repeatable. |

## Environment commands

| Command | Description |
| --- | --- |
| `agentseek plugin install [SPECS]...` | Install plugins, or sync the plugin environment when no spec is given. |
| `agentseek plugin uninstall PACKAGES...` | Remove plugins from the AgentSeek environment. |
| `agentseek plugin update [PACKAGES]...` | Update selected plugins, or all plugins when no package is given. |
| `agentseek onboard` | Run interactive runtime configuration. |
| `agentseek login` | Run the base Bub authentication flow. |
| `agentseek mcp` | Manage MCP configuration when the MCP plugin is installed and loaded. |

## Service commands

| Command | Description |
| --- | --- |
| `agentseek api` | Forward commands to `agentseek-api` when installed. |
| `agentseek ctx` | Forward commands to ContextSeek when installed. |
| `agentseek skills` | Manage skills through `npx-skills`. |

### `agentseek skills`

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--dir` | path | current working directory | Workspace directory. |

| Subcommand | Description |
| --- | --- |
| `add` | Install AgentSeek skills by default, or use an explicit source. |
| `list` | List the embedded AgentSeek catalogue, or pass arguments through. |
| `find` | Forward to `npx-skills`. |
| `update` | Forward to `npx-skills`. |
| `remove` | Forward to `npx-skills`. |
| `init` | Forward to `npx-skills`. |
