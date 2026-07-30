<div align="center">

<h1>AgentSeek</h1>

<p><strong>发现 · 创建 · 运行 · 观测 · 迭代</strong></p>

<p>
  <a href="https://github.com/ob-labs/agentseek/stargazers"><img alt="GitHub Star" src="https://img.shields.io/github/stars/ob-labs/agentseek?style=flat-square&logo=github" /></a>
  <a href="https://github.com/ob-labs/agentseek/releases"><img alt="GitHub 发布版本" src="https://img.shields.io/github/v/release/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://pypi.org/project/agentseek/"><img alt="PyPI 版本" src="https://img.shields.io/pypi/v/agentseek?style=flat-square&logo=pypi" /></a>
  <a href="https://pypi.org/project/agentseek/"><img alt="Python 版本" src="https://img.shields.io/pypi/pyversions/agentseek?style=flat-square&logo=python" /></a>
  <a href="https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain"><img alt="构建状态" src="https://img.shields.io/github/actions/workflow/status/ob-labs/agentseek/main.yml?branch=main&style=flat-square&label=CI" /></a>
  <br />
  <a href="https://github.com/ob-labs/agentseek/graphs/contributors"><img alt="贡献者" src="https://img.shields.io/github/contributors/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://github.com/ob-labs/agentseek/issues"><img alt="待处理 Issue" src="https://img.shields.io/github/issues/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE"><img alt="许可证" src="https://img.shields.io/github/license/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://ob-labs.github.io/agentseek/"><img alt="文档" src="https://img.shields.io/badge/docs-AgentSeek-0ea5e9?style=flat-square" /></a>
</p>

<p>面向可编辑本地 Agent 应用及其完整开发生命周期的 template-first 工具。</p>

<p><a href="README.md">English</a> · <a href="README.zh.md">中文</a></p>

[体验本地 ADLC](#experience-adlc) · [什么是 AgentSeek？](#what-is-agentseek) · [开发生命周期](#agent-development-lifecycle) · [引导式模板](#guided-templates) · [社区](#community)

[开发](#development)

<p>⭐ <a href="https://github.com/ob-labs/agentseek/stargazers">为 AgentSeek 点亮 Star，关注项目进展。</a></p>

<hr />

</div>

AgentSeek 是面向本地 Agent 应用开发的 template-first 工具包。它为可编辑的生成项目
提供一条可预期的生命周期：发现、创建、审视、配置、检查、运行、观测和迭代。

AgentSeek 0.1.1 从不可变的
[`agentseek-ai/agentseek-templates` catalog](https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0)
解析 lifecycle-v2 模板。CLI 用内嵌注册表快照列出模板；命名模板内容只按精确锁定的
commit 获取。

<a id="experience-adlc"></a>

## 体验本地 ADLC

从随附的 `deepagents/research` 示例开始。它会创建一个可继续编辑的 DeepAgents 调研
应用：原生 LangGraph 后端负责运行，React 前端提供主要使用体验。

```bash
# 安装生命周期 CLI，创建并进入生成出的项目。
uv tool install agentseek
agentseek create deepagents/research --no-input
cd research_deepagent

# 先检查声明的入口，再配置本地凭证。
agentseek info
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

# 运行项目声明的准备任务，然后检查就绪状态。
agentseek task --list
agentseek task sync
agentseek task frontend
agentseek doctor

# 预览原生命令，启动本地栈，并检查正在运行的服务。
agentseek dev --dry-run
agentseek dev
# agentseek dev 启动后，在另一个终端中检查实时服务。
agentseek doctor --live
```

当前 scaffold 只声明 `sync` 和 `frontend` 两个准备任务。原生后端会解析为
`uv run langgraph dev --port 2024 --no-browser`；前端则会在 `frontend/` 中解析为
`npm run dev`。

如果只想临时试用，可用 `uvx agentseek create deepagents/research --no-input` 代替安装
CLI。

<a id="what-is-agentseek"></a>

## 什么是 AgentSeek？

AgentSeek 为生成项目提供稳定的生命周期命令面；它不拥有项目源代码，也不替项目选择
框架、运行时或部署方式。模板决定这些组成部分，生成后的项目始终可以由你继续编辑。

![AgentSeek 架构](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-architecture-zh.svg)

CLI 连接开发者、编码 Agent 和桌面客户端，连接到锁定且版本化的模板 catalog，以及
可编辑项目的生命周期契约。项目自己拥有运行时和集成，包括模型、工具、MCP server
和外部服务。

<a id="agent-development-lifecycle"></a>

## Agent 开发生命周期

本地 ADLC 将迭代固定在已有项目上，而不是每次重新创建：发现、创建、审视、配置、
检查、运行、观测，再迭代回到审视。

![Agent 开发生命周期](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-adlc-zh.svg)

| 阶段 | 本地命令或项目界面 |
| --- | --- |
| 发现 | `agentseek create --list-templates` 按目标查找模板。 |
| 创建 | `agentseek create` 渲染可继续编辑的项目。 |
| 审视 | `agentseek info` 展示声明的入口和拓扑。 |
| 配置 | `.env` 和项目配置提供运行时凭证与选择。 |
| 检查 | `agentseek doctor` 验证本地就绪状态。 |
| 运行 | `agentseek dev` 启动模板拥有的本地栈。 |
| 观测 | `agentseek doctor --live` 和生命周期信号展示当前状态。 |
| 迭代 | 修改生成的项目，然后回到**审视**。 |

## 贯穿全流程的可观测性

生命周期诊断回答声明的项目是否就绪和正在运行：`agentseek info` 展示拓扑，
`agentseek doctor` 执行启动前检查，`agentseek doctor --live` 在启动后检查声明的服务。
Desktop、脚本或其他机器消费者应使用版本化 JSON 契约，而不是解析面向人的输出。

```bash
agentseek info --json
agentseek doctor --json
agentseek doctor --live --json
AGENTSEEK_CONSOLE=true agentseek doctor --live
```

`info --json` 会给出规范化服务、参考链接和安全动作，例如哪个 URL 可以直接打开；
它不会包含环境变量值或原始 process/task command。`AGENTSEEK_CONSOLE=true` 会启用
本地 CLI spans 和生命周期事件。可选的 LangSmith tracing 使用
`deepagents/research` 已有的设置，回答一次运行内部 Agent 做了什么。

<a id="guided-templates"></a>

## 引导式模板

按目标选择，再在创建前查看具体模板。AgentSeek 维护了许多模板，你不必记住整份
catalog 才能开始。

```bash
agentseek create --list-templates
agentseek create --list-templates --filter deepagents
agentseek create deepagents/research --describe
```

## 核心概念与命令

| 概念 | 提供的能力 |
| --- | --- |
| 模板 | 带有自选运行时的完整、可编辑应用脚手架。 |
| 生命周期文件 | 项目拥有的声明：路径、环境检查、服务、进程和任务。 |
| AgentSeek CLI | 为已声明生命周期提供一致的本地接口。 |

| 命令 | 用途 |
| --- | --- |
| `create` | 渲染应用模板。 |
| `info` | 展示声明的入口和生命周期元数据。 |
| `task` | 运行项目定义的准备任务。 |
| `doctor` | 检查本地就绪状态或已声明服务的实时健康度。 |
| `dev` | 启动本地开发栈。 |

## 文档

- [文档首页](https://ob-labs.github.io/agentseek/zh/)
- [快速开始](https://ob-labs.github.io/agentseek/zh/get-started/)
- [指南](https://ob-labs.github.io/agentseek/zh/guides/)
- [参考](https://ob-labs.github.io/agentseek/zh/reference/)
- [概念](https://ob-labs.github.io/agentseek/zh/concepts/)

<a id="community"></a>

## 🌐 下一步与社区

欢迎查看 **《Deep Agents 实战》**：一门基于 AgentSeek 实验的免费 LangChain /
DeepAgents 课程，见[课程仓库](https://github.com/datawhalechina/deepagents-in-action/)。
你也可以阅读[文档](https://ob-labs.github.io/agentseek/zh/)，参与
[GitHub Discussions](https://github.com/ob-labs/agentseek/discussions)，
[浏览或提交 Issue](https://github.com/ob-labs/agentseek/issues)，或参照
[贡献指南](https://github.com/ob-labs/agentseek/blob/HEAD/CONTRIBUTING.md)。

<div align="center">
  <a href="https://github.com/ob-labs/agentseek/discussions"><img alt="GitHub Discussions" src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" /></a>
  <a href="https://github.com/ob-labs/agentseek/blob/HEAD/CONTRIBUTING.md"><img alt="为 AgentSeek 贡献" src="https://img.shields.io/badge/Contribute-AgentSeek-0ea5e9?style=for-the-badge" /></a>
</div>

---

<a id="development"></a>

## 🛠️ 开发

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
make install
make check
make test
make docs-test
```

### 贡献

欢迎提交改进、修复和模板贡献。

<div align="center">
  <a href="https://github.com/ob-labs/agentseek/graphs/contributors"><img alt="AgentSeek 贡献者" src="https://contrib.rocks/image?repo=ob-labs/agentseek&max=400" /></a>
</div>

---

## 📄 许可证

[Apache-2.0](https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE)
