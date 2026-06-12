---
title: 如何安装一个 plugin
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/plugin.py
  - src/agentseek/env.py
---

# 如何安装一个 plugin

当你要向 AgentSeek workspace 添加 Bub 兼容 plugin 时使用本页。

## 前置条件

- AgentSeek 可通过 `agentseek` 调用。
- 能访问 git URL 或 Bub contrib registry。

## 步骤

1. 选择 plugin spec。

   ```text
   bub-feishu@main
   ob-labs/agentseek
   https://github.com/example/plugin.git
   agentseek-contextseek
   ```

2. 如果不想把 plugin sandbox 放在 workspace 下，钉住它的位置。

   ```bash title=".env"
   AGENTSEEK_PROJECT=/home/me/.config/agentseek/plugin-sandbox
   ```

3. 安装 plugin。

   ```bash
   agentseek plugin install bub-feishu@main
   ```

4. 检查 sandbox 包文件。

   ```bash
   cat "${BUB_PROJECT:-${AGENTSEEK_PROJECT:-.agentseek/agentseek-project}}/pyproject.toml"
   ```

## 移除一个 plugin

```bash
agentseek plugin uninstall <package-name>
```

`PACKAGES` 是 sandbox `pyproject.toml` 中列出的发行包名。

## 更新一个 plugin

```bash
agentseek plugin update              # update all
agentseek plugin update bub-feishu   # update one
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| plugin 安装到了错误位置 | 设置了其他 project 路径。 | 检查 `AGENTSEEK_PROJECT` 与 `BUB_PROJECT`。 |
| plugin 已安装但未加载 | runtime 读取了另一个 sandbox。 | 用同一个 project 路径启动 runtime。 |

## 回退

卸载该包，或删除 `${AGENTSEEK_PROJECT}` 丢弃整个 sandbox。下一次安装会重新创建。

## 相关

- 操作指南: [如何编写一个 contrib plugin](author-a-contrib-plugin.zh.md), [如何添加 skill](add-skills.zh.md)
- 参考: [CLI 参考](../reference/cli.zh.md), [文件布局参考](../reference/file-layout.zh.md)
- 概念: [扩展模型](../explanation/extension-model.zh.md)
