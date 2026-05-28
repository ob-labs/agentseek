---
title: 参考索引
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
---

# 参考

运行时行为的查阅表。参考页面镜像每页 `sources:` 块所列源文件中的事实。当出现漂移时，以源文件为准。

| 页面 | 镜像内容 |
| --- | --- |
| `environment.md` | `src/agentseek/env.py` — `AGENTSEEK_*` / `BUB_*` 别名。 |
| `cli.md` | `src/agentseek/cli.py` 以及 `agentseek <subcommand> --help`。 |
| `file-layout.md` | `.agentseek/`、`.agents/`、plugin sandbox。 |
| `packages.md` | `pyproject.toml` — extras、workspace 成员、contrib 入口点。 |
| `templates.md` | `templates/index.json` 以及各个 `templates/<framework>/<name>/`。 |
| `docker.md` | `entrypoint.sh`、`docker-compose.yml`、`Dockerfile`。 |

## 另请参阅

- 操作指南：`../how-to/index.md`
- 概念解释：`../explanation/index.md`
