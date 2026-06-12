---
title: CLI 参考
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

# CLI 参考

```text
agentseek [OPTIONS] COMMAND [ARGS]...
```

## 命令组

| 区域 | 命令 |
| --- | --- |
| Project | `create`, `run`, `build`, `deploy` |
| Runtime | `chat`, `turn`, `gateway` |
| Environment | `plugin`, `onboard`, `login`, 可选 `mcp` |
| Services | `api`, `ctx`, `skills` |
| Utility | `version` |

## 项目命令

### `agentseek create [SPEC]`

| 参数 / 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `spec` | text | - | Framework type、`type/name`、git URL 或本地路径。 |
| `--template` | text | - | 所选 type 下的模板名；不带值时列出模板。 |
| `--checkout` | text | - | 远程模板的 branch、tag 或 commit。 |
| `--list-templates` | flag | off | 列出模板并退出。 |
| `--no-input` | flag | off | 不显示 prompt，使用模板默认值。 |

### `agentseek run`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--port` | integer | `$PORT` 或 `3000` | 前端端口。 |
| `--host` | text | `127.0.0.1` | Readiness probe host。 |
| `--no-browser` | flag | off | 不打开默认浏览器。 |
| `--wait-timeout` | integer | `30` | 等待前端 ready 的秒数。 |
| `--mode` | `auto`, `compose`, `python` | `auto` | 启动模式。 |

### `agentseek build`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--tag`, `-t` | text | `<cwd-slug>:latest` | 镜像 tag。 |
| `--file`, `-f` | path | `Dockerfile` | Dockerfile 路径。 |
| `--context` | path | `.` | 构建上下文。 |
| `--platform` | text | - | 逗号分隔的目标平台。 |
| `--push` | flag | off | 构建成功后推送。 |
| `--no-cache` | flag | off | 禁用构建缓存。 |
| `--build-arg` | text | repeatable | 构建期 `KEY=VALUE` 变量。 |
| `--dry-run` | flag | off | 打印解析后的 Docker 命令，不执行。 |

### `agentseek deploy`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--dry-run` | flag | required | 生成 manifest 文件，不执行 apply。 |
| `--mode` | `docker-compose`, `k8s`, `both` | `both` | Manifest 目标。 |
| `--output` | directory | `deploy` | 输出目录。 |
| `--image` | text | `<project-slug>:latest` | 容器镜像引用。 |
| `--slug` | text | 从 cwd 推导 | Service 或 deployment 名称前缀。 |
| `--port` | integer | `8000` | 服务端口。 |
| `--replicas` | integer | `1` | Kubernetes replica 数量。 |
| `--namespace` | text | `default` | Kubernetes namespace。 |

## 运行时命令

### `agentseek chat`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--chat-id` | text | `local` | Chat id。 |
| `--session-id` | text | - | 可选 session id。 |

### `agentseek turn MESSAGE`

| 参数 / 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `MESSAGE` | text | required | 输入消息内容。 |
| `--channel` | text | `cli` | Message channel。 |
| `--chat-id` | text | `local` | Chat id。 |
| `--sender-id` | text | `human` | Sender id。 |
| `--session-id` | text | - | 可选 session id。 |

### `agentseek gateway`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--enable-channel` | text | all | 要启用的 channel；可重复。 |

## 环境命令

| 命令 | 说明 |
| --- | --- |
| `agentseek plugin install [SPECS]...` | 安装插件；未给 spec 时同步 plugin environment。 |
| `agentseek plugin uninstall PACKAGES...` | 从 AgentSeek environment 移除插件。 |
| `agentseek plugin update [PACKAGES]...` | 更新指定插件；未给 package 时更新全部插件。 |
| `agentseek onboard` | 运行交互式 runtime 配置。 |
| `agentseek login` | 运行基础 Bub authentication flow。 |
| `agentseek mcp` | 当 MCP plugin 已安装并加载时，管理 MCP 配置。 |

## 服务命令

| 命令 | 说明 |
| --- | --- |
| `agentseek api` | 在已安装 `agentseek-api` 时转发命令。 |
| `agentseek ctx` | 在已安装 ContextSeek 时转发命令。 |
| `agentseek skills` | 通过 `npx-skills` 管理 skills。 |

### `agentseek skills`

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--dir` | path | 当前工作目录 | Workspace 目录。 |

| 子命令 | 说明 |
| --- | --- |
| `add` | 默认安装 AgentSeek skills，或使用显式 source。 |
| `list` | 列出内置 AgentSeek catalogue，或透传参数。 |
| `find` | 转发到 `npx-skills`。 |
| `update` | 转发到 `npx-skills`。 |
| `remove` | 转发到 `npx-skills`。 |
| `init` | 转发到 `npx-skills`。 |
