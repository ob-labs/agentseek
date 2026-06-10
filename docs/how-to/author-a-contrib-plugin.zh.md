---
title: 如何编写一个 contrib plugin
type: how-to
audience: [A3]
runs: no
verified_on: 2026-05-28
sources:
  - contrib/README.md
  - pyproject.toml
---

# 如何编写一个 contrib plugin

当你需要在本 monorepo 中以 `contrib/agentseek-<feature>/` 形式存在的
Bub 兼容 plugin 时使用本指南。plugin 契约、README 结构与
分发约定由 [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) 维护 —— 本页
指向那份文档，并列出 agentseek 特有的不可省略环节。

## 前置条件

- 先阅读 [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)。它是 README 标准的
  唯一权威来源。
- 决定你的 plugin 属于哪个 Bub entry point 组 (`[project.entry-points.bub]`)。

## 步骤

1. 在 `contrib/agentseek-<feature>/` 下创建 workspace 成员，并将其
   加入 `pyproject.toml:101` 的 workspace 列表：

   ```toml title="pyproject.toml"
   [tool.uv.workspace]
   members = [
     # ... existing members
     "contrib/agentseek-<feature>",
     ".agentseek/agentseek-project",
   ]
   ```

2. 遵循 contrib 的 **命名约定**
   ([contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md), "agentseek follows Bub's extension conventions")：

   | 项 | 约定 |
   | --- | --- |
   | 发行包名 | `agentseek-<feature>` |
   | Python 包 | `agentseek_<feature>` |
   | Bub entry point 组 | `[project.entry-points.bub]` |
   | 环境变量 | 优先 `AGENTSEEK_*`；对 Bub 运行时设置接受 `BUB_*` |
   | 两种前缀同时存在时 | `BUB_*` 优先 (与 `apply_agentseek_env_aliases` 一致，`src/agentseek/env.py:63`) |

3. 按照 [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) 的章节顺序 ("README Standard")
   编写 README：

   1. `At A Glance`
   2. `When To Use It`
   3. `Install`
   4. `Configure`
   5. `Run`
   6. `Runtime Behavior`
   7. `Verify`
   8. `Limitations`

4. (可选) 在根 `pyproject.toml:27` 中将该包暴露为 extra：

   ```toml title="pyproject.toml"
   [project.optional-dependencies]
   <feature> = ["agentseek-<feature>"]
   ```

   并在 `[tool.uv.sources]` 中钉住 workspace 来源
   (`pyproject.toml:87`)：

   ```toml
   agentseek-<feature> = { workspace = true }
   ```

5. 使用捆绑的 `plugin-creator` skill 来脚手架包结构。
   agentseek 改造版镜像了上游 Bub 的 contrib 流程，但
   专门针对 `contrib/agentseek-*`、`AGENTSEEK_*` 别名以及捆绑的
   `src/skills` (参见 [扩展模型](../explanation/extension-model.zh.md))。

### CLI 快捷方式

没有 `agentseek plugin new` 命令。请在 chat session 中使用
`plugin-creator` skill，或者复制已有的 `contrib/agentseek-*/` 再
重命名。

## 边界

- **不要** 把每个包的 README 复制进 `docs/`。改为交叉链接。
- 主 `docs/` 树只记录 `src/agentseek` 和 `src/skills`
  ([contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md), "Documentation Boundary")。

## 相关

- contrib 标准: [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
- 操作指南: [如何安装插件](install-a-plugin.zh.md), [如何添加 skill](add-skills.zh.md)
- 参考: [包参考](../reference/packages.zh.md)
- 概念: [扩展模型](../explanation/extension-model.zh.md)
