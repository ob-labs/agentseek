---
title: 如何安装一个 plugin
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/env.py
---

# 如何安装一个 plugin

当你需要向 agentseek workspace 添加新的 Bub 兼容 plugin (channel、
模型 provider、store、工具包、调度器等) 时使用本指南。
plugin 会安装到 **plugin sandbox**，即位于 `AGENTSEEK_PROJECT` /
`BUB_PROJECT` 的 uv 管理项目中。

## 前置条件

- 已安装 agentseek，并在 `PATH` 上可作为 `uv run agentseek` 调用。
- 具备网络访问 —— `agentseek install` 会解析 git URL 与 Bub contrib
  registry。

## 步骤

1. 选择 plugin spec。`agentseek install` 接受 (`reference/cli.md#agentseek-install-specs`)：

   - 一个 git URL
   - `owner/repo`
   - `bub-contrib` 中的包名 (通常是 `name@branch`)

   它 **不是** 针对任意发行名的通用 PyPI 安装器。

2. (可选) 钉住 sandbox 位置。默认是
   `${BUB_HOME}/agentseek-project` (`src/agentseek/env.py:72`)。如果想
   让 plugin 不进入你的仓库，设置：

   ```bash title=".env"
   AGENTSEEK_PROJECT=/home/me/.config/agentseek/plugin-sandbox
   ```

3. 安装 plugin。第一次调用通过
   `uv init --bare --name agentseek-project --app` 初始化 sandbox，并加入 Bub
   依赖 (`src/agentseek/cli.py:134`)。

   ```bash title="not executed in this run"
   uv run agentseek install bub-feishu@main
   ```

4. 验证 sandbox 现在列出了该 plugin：

   ```bash title="not executed in this run"
   cat "${BUB_PROJECT:-.agentseek/agentseek-project}/pyproject.toml"
   ```

### CLI 快捷方式

对于安装而言，库形式 **就是** CLI 形式。没有嵌入式 API；
`agentseek install` 会在 sandbox 内 shell out 到 `uv`。

上游 Bub 的 `bub install <spec>` 等效。agentseek CLI
仅添加了 sandbox 默认值与品牌化。

## 移除一个 plugin

```bash title="not executed in this run"
uv run agentseek uninstall <package-name>
```

`PACKAGES` 是 sandbox `pyproject.toml` 中列出的发行包名。

## 更新 plugin

```bash title="not executed in this run"
uv run agentseek update              # update all
uv run agentseek update bub-feishu   # update one
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 首次安装报 `FileNotFoundError` | sandbox 路径缺失 | agentseek 的 `_ensure_plugin_sandbox` (`src/agentseek/cli.py:123`) 会创建它；若仍出现，请提 bug。 |
| plugin 已加载但未被运行时识别 | plugin 在 sandbox 中，但运行时读取了不同的 `BUB_PROJECT` | 确认 `${BUB_PROJECT}` 与安装目标路径一致。 |

## 回退

`uv run agentseek uninstall <name>` 从 sandbox 中移除该包。如要丢弃
整个 sandbox，删除 `${AGENTSEEK_PROJECT}` (默认
`.agentseek/agentseek-project`)。下一次安装会重新构建。

## 相关

- 操作指南: [How to author a contrib plugin](author-a-contrib-plugin.md), [How to add skills](add-skills.md)
- 参考: [CLI reference](../reference/cli.md), [File layout reference](../reference/file-layout.md)
- 概念: [The extension model](../explanation/extension-model.md)
