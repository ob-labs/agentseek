---
title: CLI 参考
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

# CLI 参考

## 用法

```bash
agentseek [OPTIONS] COMMAND [ARGS]...
```

命令按功能分组：

| 区域 | 命令 | 用途 |
| --- | --- | --- |
| Project | `create`, `run`, `build`, `deploy` | 创建、运行、构建和打包项目。 |
| Runtime | `chat`, `turn`, `gateway` | 与 harness 交互。 |
| Environment | `plugin`, `mcp`, `onboard`, `login` | 管理运行时配置和插件。 |
| Services | `api`, `ctx`, `skills` | 桥接可选服务和 skill 工具。 |

## 项目管理

### `agentseek create [SPEC]`

从内置或外部模板创建项目。

| 参数 / 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `spec` | TEXT | - | 模板 family、`family/name`、git URL 或本地路径。 |
| `--template` | TEXT | - | 所选 family 下的模板名。 |
| `--checkout` | TEXT | - | 远程模板的 branch、tag 或 commit。 |
| `--list-templates` | flag | off | 列出模板并退出。 |
| `--no-input` | flag | off | 跳过 Cookiecutter 交互提示。 |

### `agentseek run`

在本地运行生成的项目。

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--port` | INTEGER | `$PORT` 或 `3000` | 前端端口。 |
| `--host` | TEXT | `127.0.0.1` | readiness probe 使用的 host。 |
| `--no-browser` | flag | off | 不打开浏览器。 |
| `--wait-timeout` | INTEGER | `30` | 等待 ready 的秒数。 |
| `--mode` | `auto\|compose\|python` | `auto` | 启动模式。 |

### `agentseek build`

把当前项目构建为容器镜像。

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--tag`, `-t` | TEXT | `<cwd-slug>:latest` | 镜像 tag。 |
| `--file`, `-f` | PATH | `Dockerfile` | Dockerfile 路径。 |
| `--context` | PATH | `.` | 构建上下文。 |
| `--platform` | TEXT | - | 逗号分隔的目标平台。 |
| `--push` | flag | off | 构建成功后推送。 |
| `--no-cache` | flag | off | 禁用构建缓存。 |
| `--build-arg` | TEXT | 可重复 | 构建期 `KEY=VALUE` 变量。 |
| `--dry-run` | flag | off | 打印解析后的 Docker 命令。 |

### `agentseek deploy`

生成部署清单。当前实现要求 `--dry-run`，因此只写文件，不执行 apply。

| 选项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--dry-run` | flag | required | 只生成清单。 |
| `--mode` | `docker-compose\|k8s\|both` | `both` | 清单目标。 |
| `--output` | DIRECTORY | `deploy` | 输出目录。 |
| `--image` | TEXT | `<project-slug>:latest` | 容器镜像引用。 |
| `--slug` | TEXT | inferred | 服务或 deployment 名称前缀。 |
| `--port` | INTEGER | `8000` | 服务端口。 |
| `--replicas` | INTEGER | `1` | Kubernetes replica 数量。 |
| `--namespace` | TEXT | `default` | Kubernetes namespace。 |

## 运行时

### `agentseek chat`

启动交互式 CLI chat，支持 MCP 和 skill。

### `agentseek turn MESSAGE`

让一条输入消息经过运行时。

### `agentseek gateway`

启动已配置 channel 的消息监听。

## 环境

### `agentseek plugin install [SPECS]...`

安装运行时插件到 AgentSeek 插件 sandbox。默认 sandbox 为
`.agentseek/agentseek-project`。

### `agentseek plugin uninstall PACKAGES...`

从插件 sandbox 移除 package。

### `agentseek plugin update [PACKAGES]...`

更新指定插件，或在未指定 package 时更新 sandbox。

### `agentseek onboard`

运行交互式配置流程并写入运行时配置。

## 服务

### `agentseek api`

在安装 `agentseek-api` 后转发 API 服务命令。

### `agentseek ctx`

在安装 ContextSeek CLI 后转发 ContextSeek 命令。

### `agentseek skills`

通过 `npx-skills` 管理 skills，必要时回退到 `npx`。

## 验证

```bash
uv run agentseek --help
uv run agentseek create --help
uv run agentseek chat --help
uv run agentseek turn --help
uv run agentseek plugin --help
```
