---
title: CLI 参考
type: reference
audience: [A1, A2, A3, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/__main__.py
  - pyproject.toml
---

# CLI 参考

本页镜像了在验证日期由 `agentseek 0.1.0` 注册的每个子命令所执行的
`uv run agentseek <subcommand> --help` 的输出。

CLI 二进制在 `pyproject.toml:49` 中注册为 `agentseek = "agentseek.__main__:app"`。

## 顶层选项

```text
Usage: agentseek [OPTIONS] COMMAND [ARGS]...
```

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `--workspace`, `-w` | TEXT | (unset) | workspace 的路径。 |
| `--help` | flag | — | 显示顶层帮助并退出。 |

## 命令

### `agentseek run`

:   完成 `.env` 配置后，在本地启动项目。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--port` | INTEGER | `.env` 中的 `$PORT`，否则为 `3000` | 前端端口。 |
    | `--host` | TEXT | `127.0.0.1` | 探测就绪状态的主机。 |
    | `--no-browser` | flag | off | 跳过打开默认浏览器。 |
    | `--wait-timeout` | INTEGER | `30` | 等待前端的秒数。 |
    | `--mode` | `auto\|compose\|python` | `auto` | 启动模式覆盖。 |

    由 `agentseek-cli` 提供（`contrib/agentseek-cli/README.md`）。

### `agentseek chat`

:   通过 CLI channel 使用 Bub 内置的 chat；agentseek 增加了 lifecycle channels
    （`src/agentseek/cli.py:83`）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--chat-id` | TEXT | `local` | Chat id。 |
    | `--session-id` | TEXT | `None` | 可选的 session id。 |

### `agentseek onboard`

:   交互式收集 plugin 配置并写入 Bub 的配置文件。使用 `src/agentseek/cli.py:23`
    中的 agentseek 品牌横幅。

    除 `--help` 外不接收其他参数。

### `agentseek gateway`

:   启动消息监听器（例如 telegram）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--enable-channel` | TEXT (repeatable) | all | 要启用的 channels。 |

### `agentseek install [SPECS]...`

:   将 plugin 安装到 Bub 的环境中，或者在没有提供规格时同步环境。agentseek 将安装
    sandbox 替换为 `DEFAULT_PLUGIN_SANDBOX = "agentseek-project"`
    （`src/agentseek/cli.py:115`、`src/agentseek/env.py:22`）。

    | 参数 / 标志 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `SPECS` | TEXT… | `[]` | Git URL、`owner/repo`，或 bub-contrib 中的 `name@branch`。 |
    | `--project` | PATH | `${BUB_PROJECT}`（默认为 `${BUB_HOME}/agentseek-project`） | project 目录的路径。 |

    帮助文本仍打印上游默认值 `~/.bub/bub-project`。运行时默认值是 agentseek sandbox，
    因为 `apply_agentseek_env_aliases` 在 Typer 读取默认值之前就设置了 `BUB_PROJECT`
    （`src/agentseek/env.py:73`）。

### `agentseek uninstall PACKAGES...`

:   从 Bub 的环境中卸载 plugin。`PACKAGES` 是必填项。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | project 目录的路径。 |

### `agentseek update [PACKAGES]...`

:   更新指定的包，或在未提供参数时更新 Bub 环境中的所有包。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | project 目录的路径。 |

### `agentseek create [SPEC]`

:   从预构建的模板（位于 `templates/` 下的 cookiecutter）创建一个新的 agent project。

    | 参数 / 标志 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `spec` | TEXT | — | 框架类型（`deepagents`、`langchain`、`bub`）、`type/name`、git URL，或本地路径。 |
    | `--template` | TEXT | — | 所选类型下的具名模板（例如 `cli-remote`）。 |
    | `--checkout` | TEXT | — | 远程拉取的 branch / tag / commit。 |
    | `--list-templates` | flag | — | 列出该类型可用的模板并退出。 |
    | `--no-input` | flag | off | 跳过 cookiecutter 的交互提示。 |

    捆绑模板列表请参见 `reference/templates.md`。由 `agentseek-cli` 提供。

### `agentseek build`

:   将 project 构建为容器镜像（封装 `docker build` / `docker buildx build`）。
    顶层命令 — 尽管 `--help` 中出现了 `COMMAND [ARGS]...` 这一行，但它没有子命令。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--tag`, `-t` | TEXT | `<cwd-slug>:latest` | 镜像 tag。 |
    | `--file`, `-f` | PATH | （由 `agentseek-cli` 解析） | Dockerfile 的路径。 |
    | `--context` | PATH | `.` | 构建上下文目录。 |
    | `--platform` | TEXT | — | 以逗号分隔的目标平台。 |
    | `--push` | flag | off | 构建成功后推送。 |
    | `--no-cache` | flag | off | 构建时不使用缓存。 |
    | `--build-arg` | TEXT (repeatable) | — | `KEY=VALUE` 形式的构建时变量。 |
    | `--dry-run` | flag | off | 打印解析后的命令而不执行。 |

### `agentseek deploy`

:   生成部署清单（docker-compose / k8s）。顶层命令 — 尽管 `--help` 中出现了
    `COMMAND [ARGS]...` 这一行，但它没有子命令。在 v1 中，`--dry-run` 是必填的。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--dry-run` | flag | v1 中必填 | 生成清单但不部署。 |
    | `--mode` | `docker-compose\|k8s\|both` | `both` | 部署目标。 |
    | `--output` | DIRECTORY | `deploy` | 清单写入位置。 |
    | `--image` | TEXT | `<project-slug>:latest` | 容器镜像引用。 |
    | `--slug` | TEXT | 从 cwd 推断 | 用于 service / deployment 名称的 project slug。 |
    | `--port` | INTEGER | `8000` | 服务端口。 |
    | `--replicas` | INTEGER (≥1) | `1` | k8s Deployment 副本数。 |
    | `--namespace` | TEXT | `default` | k8s namespace。 |

### `agentseek api`

:   当安装了 `agentseek-api` 时，将 API 运行时命令转发给它。若环境中没有
    `agentseek-api`，所有子命令都会失败并提示：

    ```text title="output"
    The `agentseek api` commands require `agentseek-api` in the current environment.
    Install it first, for example: `uv pip install -e references/agentseek-api`.
    ```

    子命令（每个都将同名命令转发给 `agentseek-api`）：
    `dev`、`serve`、`dockerfile`、`build`、`up`、`version`。

### `agentseek ctx`

:   ContextSeek — 语义上下文层。转发给 `contextseek` CLI。
    当安装了 `agentseek[context]`（或 `agentseek-contextseek`）时可用。
    子命令包括 `add`、`retrieve`、`expand`、`compact`、
    `forget`、`delete`、`overview`、`tools`、`metrics`、`dream`、`feedback`、
    `upstream`、`evidence-chain`、`chain-confidence`、`skill-tools`、
    `skill-context`、`skill-import`、`items`。

    用法参见 `../how-to/use-contextseek.md` 以及 [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)。

### `agentseek skills`

:   通过上游 `vercel-labs/skills` CLI 管理 agent skills（使用 `npx` 运行）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--dir` | PATH | `$PWD` | 运行 `skills` 的 workspace 目录。 |

    子命令（每个都转发给 `npx skills`）：`add`、`list`、`find`、
    `update`、`remove`、`init`。

### `agentseek login`

:   认证命令。

    子命令：`openai` — 使用 OpenAI OAuth 登录。

    `agentseek login openai` 的参数：

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--codex-home` | PATH | — | 存储 Codex OAuth 凭证的目录。 |
    | `--browser` / `--no-browser` | flag | `--browser` | 在浏览器中打开 OAuth URL。 |
    | `--manual` | flag | off | 粘贴 callback URL 或 code，而不是运行本地回调服务器。 |
    | `--timeout` | FLOAT | `300.0` | OAuth 等待超时（秒）。 |

## 实际执行的 help 命令

以下命令是从仓库根目录运行以填充本页内容的：

```bash
uv run agentseek --help
uv run agentseek run --help
uv run agentseek chat --help
uv run agentseek onboard --help
uv run agentseek gateway --help
uv run agentseek install --help
uv run agentseek uninstall --help
uv run agentseek update --help
uv run agentseek create --help
uv run agentseek build --help
uv run agentseek deploy --help
uv run agentseek api --help
uv run agentseek api dev --help
uv run agentseek ctx --help
uv run agentseek skills --help
uv run agentseek skills add --help
uv run agentseek login --help
uv run agentseek login openai --help
```

## 另请参阅

- 操作指南：`../how-to/install-a-plugin.md`、`../how-to/run-locally.md`、
  `../how-to/run-gateway.md`、`../how-to/build-and-deploy.md`
- 参考：`environment.md`、`packages.md`
