---
title: 如何构建和部署
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/lifecycle/commands/build.py
  - src/agentseek/lifecycle/commands/deploy.py
  - Dockerfile
---

# 如何构建和部署

当你已经有一个生成项目，并且需要容器镜像与 Compose / Kubernetes 清单时使用本页。

## 前置条件

- 项目环境中已经安装 `agentseek`。
- 已安装 `docker`，需要多平台构建时还需要 `docker buildx`。
- 当前 `deploy` 实现要求 `--dry-run`。

## 构建镜像

```bash title="not executed in this run"
uv run agentseek build --tag my-agent:0.1.0
```

只打印 Docker 命令：

```bash title="not executed in this run"
uv run agentseek build --dry-run --tag my-agent:0.1.0
```

常用选项：

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `--tag`, `-t` | `<cwd-slug>:latest` | 镜像 tag。 |
| `--file`, `-f` | `Dockerfile` | Dockerfile 路径。 |
| `--context` | `.` | 构建上下文。 |
| `--platform` | - | 逗号分隔的目标平台。 |
| `--push` | off | 构建成功后推送。 |
| `--no-cache` | off | 跳过缓存。 |
| `--build-arg KEY=VALUE` | - | 可重复的构建期变量。 |
| `--dry-run` | off | 只打印，不执行。 |

## 生成部署清单

```bash title="not executed in this run"
uv run agentseek deploy --dry-run --image my-agent:0.1.0
```

常用选项：

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `--dry-run` | required | 只生成清单，不 apply。 |
| `--mode` | `both` | `docker-compose`、`k8s` 或 `both`。 |
| `--output` | `deploy` | 输出目录。 |
| `--image` | `<project-slug>:latest` | 容器镜像引用。 |
| `--slug` | inferred | 服务或 deployment 名称前缀。 |
| `--port` | `8000` | 服务端口。 |
| `--replicas` | `1` | Kubernetes replicas。 |
| `--namespace` | `default` | Kubernetes namespace。 |

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 找不到 `agentseek build` | 项目环境尚未同步 | 先运行 `uv sync`，再用 `uv run agentseek build`。 |
| `--push` 返回 `unauthorized` | 未登录 registry | 先运行 `docker login <registry>`。 |
| `agentseek deploy` 缺少 `--dry-run` 报错 | 当前 deploy 只写文件 | 加上 `--dry-run`。 |
| 清单里的镜像不对 | 未设置 `--image` | 传入 `--image my-agent:0.1.0`。 |

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [Docker 参考](../reference/docker.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
