---
hide_sidebar: true
---

<div class="landing-hero">
  <p class="landing-kicker">$ agentseek</p>
  <h1>面向真实项目封装的数据库原生 Agent Runtime</h1>
  <p class="landing-lead">
    agentseek 在 Bub 之上提供项目级默认配置、`AGENTSEEK_*` 别名、内置技能以及以工作区为中心的运行时布局。
  </p>
  <div class="landing-actions">
    <a class="terminal-button primary" href="docs/getting-started/">快速开始</a>
    <a class="terminal-button" href="docs/">阅读文档</a>
    <a class="terminal-button" href="hub/">浏览目录</a>
  </div>
</div>

## 快速开始

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

先配置一个模型，再启动本地会话：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

## 可以从这里继续

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="docs/">文档</a></h3>
    <p>查看主发行版的安装、配置和扩展说明。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="hub/">目录</a></h3>
    <p>浏览本仓库以及更广泛 Bub 生态中的插件、技能和相关链接。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="blog/">博客</a></h3>
    <p>阅读项目介绍、迁移说明以及围绕真实工作流的实践文章。</p>
  </div>
</div>
