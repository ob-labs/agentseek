---
title: 如何构建和部署
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/commands/build.py
  - src/agentseek/cli/commands/deploy.py
  - Dockerfile
---

# 如何构建和部署

当你已有生成项目，并需要可部署产物时使用本页。

## 前置条件

- 在生成项目根目录运行命令。
- 项目中已有 `Dockerfile`。
- 已安装 Docker。

## 构建镜像

```bash
uv run agentseek build --tag my-agent:0.1.0
```

需要检查路径或 tag 时，先预览 Docker 命令：

```bash
uv run agentseek build --dry-run --tag my-agent:0.1.0
```

registry 登录就绪后，可以构建并推送：

```bash
uv run agentseek build --tag registry.example.com/my-agent:0.1.0 --push
```

## 生成部署清单

```bash
uv run agentseek deploy --dry-run --image my-agent:0.1.0
```

```text title="output"
wrote deploy/docker-compose.yaml
wrote deploy/k8s/deployment.yaml
wrote deploy/k8s/service.yaml
agentseek deploy --dry-run --mode both → 3 file(s) under deploy (image=my-agent:0.1.0, slug=my-bub-agent).
```

只需要一种目标时，指定 mode：

```bash
uv run agentseek deploy --dry-run --mode k8s --image my-agent:0.1.0
```

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 找不到 `agentseek build` | 当前项目未安装 AgentSeek。 | 运行 `uv add agentseek`，再用 `uv run agentseek build`。 |
| `--push` 返回 `unauthorized` | 未登录 registry。 | 运行 `docker login <registry>`。 |
| `deploy` 拒绝执行 | 需要 `--dry-run`。 | 加上 `--dry-run`。 |
| 清单里的镜像不对 | 未设置 `--image`。 | 显式传入镜像名。 |

## 回退

如果不想保留清单，删除生成的 `deploy/` 目录。

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
