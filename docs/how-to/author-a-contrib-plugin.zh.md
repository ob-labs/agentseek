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

当你要在 `contrib/agentseek-<feature>/` 下添加 Bub 兼容 plugin 时使用本页。

## 前置条件

- 阅读 [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)。
- 决定该 plugin 注册哪个 Bub hook 或 entry point。

## 步骤

1. 创建 `contrib/agentseek-<feature>/`。

2. 将它加入根 workspace。

   ```toml title="pyproject.toml"
   [tool.uv.workspace]
   members = [
     # ... existing members
     "contrib/agentseek-<feature>",
     ".agentseek/agentseek-project",
   ]
   ```

3. 使用标准命名。

   | 项 | 约定 |
   | --- | --- |
   | 发行包名 | `agentseek-<feature>` |
   | Python 包 | `agentseek_<feature>` |
   | Bub entry point 组 | `[project.entry-points.bub]` |
   | 环境变量 | 优先 `AGENTSEEK_*`；对 Bub 运行时设置接受 `BUB_*` |

4. 按这些章节写包 README。

   1. `At A Glance`
   2. `When To Use It`
   3. `Install`
   4. `Configure`
   5. `Run`
   6. `Runtime Behavior`
   7. `Verify`
   8. `Limitations`

5. 如果希望开发者从根项目安装它，将该包暴露为 optional dependency。

   ```toml title="pyproject.toml"
   [project.optional-dependencies]
   <feature> = ["agentseek-<feature>"]
   ```

6. 钉住 workspace 来源。

   ```toml
   agentseek-<feature> = { workspace = true }
   ```

### CLI 快捷方式

没有 `agentseek plugin new` 命令。使用 `plugin-creator` skill，或复制已有的
`contrib/agentseek-*/` 包并重命名。

## 边界

- 包特定文档留在包 README。
- `docs/` 中只链接 contrib README，不复制内容。

## 相关

- contrib 标准: [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
- 操作指南: [如何安装插件](install-a-plugin.zh.md), [如何添加 skill](add-skills.zh.md)
- 参考: [包参考](../reference/packages.zh.md)
- 概念: [扩展模型](../explanation/extension-model.zh.md)
