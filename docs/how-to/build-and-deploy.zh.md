---
title: 如何构建与部署
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - contrib/agentseek-cli/README.md
  - Dockerfile
---

# 如何构建与部署

当你已经有一个生成好的项目 (参见
`../reference/templates.md`)，想把它打成容器镜像并产出一组
Compose / Kubernetes manifest 时使用本指南。两个命令均由
`agentseek-cli` 提供 (`pyproject.toml:31`)。

## 前置条件

- 已安装 `agentseek[cli]` (或激活了 `agentseek-cli` workspace 成员)。
- `build` 需要 `docker` (可选 `docker buildx`)。
- `deploy` 运行时无任何依赖 —— v1 中 `--dry-run` 是必填，命令
  只会写出 manifest。

## 构建容器镜像

1. 在项目根目录构建：

   ```bash title="not executed in this run"
   uv run agentseek build --tag my-agent:0.1.0
   ```

   TODO(reviewer): execute against a Docker daemon to capture buildx output.

2. 标志位 (来自 `agentseek build --help`)：

   | 标志 | 默认值 | 描述 |
   | --- | --- | --- |
   | `--tag`, `-t` | `<cwd-slug>:latest` | 镜像 tag。 |
   | `--file`, `-f` | 由 `agentseek-cli` 解析 | Dockerfile 路径。 |
   | `--context` | `.` | 构建上下文目录。 |
   | `--platform` | — | 逗号分隔的目标，如 `linux/amd64,linux/arm64`。 |
   | `--push` | off | 构建后推送 (需先登录 registry)。 |
   | `--no-cache` | off | 跳过缓存。 |
   | `--build-arg KEY=VALUE` | — | 可重复的构建期变量。 |
   | `--dry-run` | off | 打印解析后的命令，不执行。 |

3. 仅打印将要执行的内容，不实际构建：

   ```bash title="not executed in this run"
   uv run agentseek build --dry-run --tag my-agent:0.1.0
   ```

## 生成部署 manifest

v1 中 `--dry-run` 是 **必填** —— 命令只写出 manifest，
不会执行部署。

1. 在 `deploy/` 下同时生成 docker-compose 与 k8s manifest：

   ```bash title="not executed in this run"
   uv run agentseek deploy --dry-run --image my-agent:0.1.0
   ```

   TODO(reviewer): capture the actual file tree written by `deploy --dry-run`
   so the page can include a sample layout.

2. 标志位 (来自 `agentseek deploy --help`)：

   | 标志 | 默认值 | 描述 |
   | --- | --- | --- |
   | `--dry-run` | 必填 | 生成 manifest 但不部署。 |
   | `--mode` | `both` | `docker-compose`、`k8s` 或 `both`。 |
   | `--output` | `deploy` | manifest 写入的目录。 |
   | `--image` | `<project-slug>:latest` | 容器镜像引用。 |
   | `--slug` | 从 cwd 推断 | service / deployment 名称使用的项目 slug。 |
   | `--port` | `8000` | service 端口。 |
   | `--replicas` | `1` | k8s Deployment 副本数 (必须 ≥ 1)。 |
   | `--namespace` | `default` | k8s 命名空间。 |

### CLI 快捷方式

这些命令 **就是** CLI 形态。等价的嵌入式调用需要直接调用
`agentseek-cli` 的 build / deploy 模块，参见
[agentseek-cli README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md)。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 找不到 `agentseek build` | 未安装 `agentseek[cli]` | `uv sync --extra cli` 或把 `agentseek-cli` 加进你的项目。 |
| `--push` 报 `unauthorized` | 未登录 registry | 先执行 `docker login <registry>`。 |
| `agentseek deploy` 没带 `--dry-run` 报错 | v1 强制要求 `--dry-run` | 加上该标志。 |
| manifest 引用了错误的镜像 | 未设置 `--image`，回退到 slug | 传入 `--image my-agent:0.1.0`。 |

## 回退

`agentseek build` 不会删除其产物。要移除已构建的镜像：

```bash title="not executed in this run"
docker image rm my-agent:0.1.0
```

`agentseek deploy --dry-run` 只写文件；若要丢弃，删除 `deploy/`
目录即可。

## 相关

- 操作指南: `run-with-docker-compose.md`
- 参考: `../reference/cli.md`, `../reference/docker.md`
- contrib: [agentseek-cli README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md)
