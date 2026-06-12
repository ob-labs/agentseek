---
title: 扩展模型
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - docs/how-to/install-a-plugin.md
  - AGENTS.md
  - contrib/README.md
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# 扩展模型

AgentSeek 提供多个扩展点，因为不是每个改动都值得写成 plugin。

真正有用的问题是：你正在改哪一类行为？

## 选择最小表面

使用能匹配改动的最小表面：

- **项目 instructions** 用于每一轮 turn 都应该遵守的持久指导。
- **Skills** 用于任务专属行为、工作流或小型辅助脚本。
- **MCP servers** 用于可以通过配置声明的外部工具。
- **Plugins** 用于 runtime hook、channel、store、model provider、scheduler 和工具包。
- **Contrib packages** 用于带有独立依赖、测试和文档的维护型集成。

这个顺序很重要。一个事实不应该变成 Python package。一个 runtime hook 也不应该藏在
prompt 里。保持表面小，项目才容易审阅。

## 这些表面有何不同

Instructions 和 skills 塑造 agent 应该知道什么、怎样完成任务。它们很容易加入
workspace。

MCP entry 暴露已经在 Python 进程外运行的工具。它们是配置，不是应用代码。

Plugins 改变 runtime。它们可以添加 channel、tool、storage、schedule 或 model 行为。
这让它们很强，也值得被打包和版本化。

Contrib packages 是足够大的 plugin 或集成，拥有自己的 README、示例、测试和依赖集合。

## 为什么需要这个模型

Agent 应用演进不均匀。今天加一条规则，明天加一个工作流，之后可能加工具，再之后是
存储后端。

扩展模型让这些变化留在正确位置，使开发者以后能找到它们，运维人员也能判断哪些变化会影响
runtime。

## 下一步

- [如何添加 skill](../how-to/add-skills.zh.md)
- [如何配置 MCP server](../how-to/configure-mcp.zh.md)
- [如何安装插件](../how-to/install-a-plugin.zh.md)
- [包参考](../reference/packages.zh.md)
