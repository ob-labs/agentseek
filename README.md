<div align="center">

<h1>AgentSeek</h1>

<p><strong>Discover · Create · Run · Observe · Iterate</strong></p>

<p>
  <a href="https://github.com/ob-labs/agentseek/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/ob-labs/agentseek?style=flat-square&logo=github" /></a>
  <a href="https://github.com/ob-labs/agentseek/releases"><img alt="GitHub release" src="https://img.shields.io/github/v/release/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://pypi.org/project/agentseek/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/agentseek?style=flat-square&logo=pypi" /></a>
  <a href="https://pypi.org/project/agentseek/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/agentseek?style=flat-square&logo=python" /></a>
  <a href="https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain"><img alt="Build status" src="https://img.shields.io/github/actions/workflow/status/ob-labs/agentseek/main.yml?branch=main&style=flat-square&label=CI" /></a>
  <br />
  <a href="https://github.com/ob-labs/agentseek/graphs/contributors"><img alt="Contributors" src="https://img.shields.io/github/contributors/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://github.com/ob-labs/agentseek/issues"><img alt="Open issues" src="https://img.shields.io/github/issues/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE"><img alt="License" src="https://img.shields.io/github/license/ob-labs/agentseek?style=flat-square" /></a>
  <a href="https://ob-labs.github.io/agentseek/"><img alt="Documentation" src="https://img.shields.io/badge/docs-AgentSeek-0ea5e9?style=flat-square" /></a>
</p>

<p>Template-first tooling for editable local agent applications and their complete development lifecycle.</p>

<p><a href="README.md">English</a> · <a href="README.zh.md">中文</a></p>

[Experience the local ADLC](#experience-adlc) · [What is AgentSeek?](#what-is-agentseek) · [Lifecycle](#agent-development-lifecycle) · [Guided templates](#guided-templates) · [Community](#community)

[Development](#development)

<p>⭐ <a href="https://github.com/ob-labs/agentseek/stargazers">Star AgentSeek to follow its progress.</a></p>

<hr />

</div>

AgentSeek is a template-first toolkit for local agent application development.
It gives editable generated projects one predictable lifecycle: discover,
create, inspect, configure, check, run, observe, and iterate.

AgentSeek 0.1.1 resolves lifecycle-v2 templates from the immutable
[`agentseek-ai/agentseek-templates` catalog](https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0).
The CLI lists templates from its embedded registry snapshot and fetches named
template content at the exact locked commit.

<a id="experience-adlc"></a>

## Experience the local ADLC

Start with the shipped `deepagents/research` walkthrough. It creates a fully
editable DeepAgents research app with a native LangGraph backend and a React frontend
as its primary user experience.

```bash
# Install the lifecycle CLI, then create and enter the generated project.
uv tool install agentseek
agentseek create deepagents/research --no-input
cd research_deepagent

# Inspect declared entry points before configuring local credentials.
agentseek info
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

# Run the setup tasks declared by this project, then check readiness.
agentseek task --list
agentseek task sync
agentseek task frontend
agentseek doctor

# Preview the native commands, run the local stack, and check live services.
agentseek dev --dry-run
agentseek dev
# In another terminal, after agentseek dev starts, check live services.
agentseek doctor --live
```

The current scaffold declares only `sync` and `frontend` setup tasks. Its
native backend resolves to `uv run langgraph dev --port 2024 --no-browser`,
while the frontend resolves to `npm run dev` in `frontend/`.

For a one-off run, use `uvx agentseek create deepagents/research --no-input`
instead of installing the CLI.

<a id="what-is-agentseek"></a>

## What is AgentSeek?

AgentSeek supplies the stable lifecycle surface around a generated project; it
does not own that project's source, framework, runtime, or deployment. A
template selects those pieces, and the generated project remains yours to edit.

![AgentSeek architecture](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-architecture-en.svg)

The CLI connects people, coding agents, and desktop clients to a locked,
versioned template catalog and an editable project lifecycle contract. The
project then owns its runtimes and integrations, including models, tools, MCP
servers, and external services.

<a id="agent-development-lifecycle"></a>

## Agent Development Lifecycle

The local ADLC keeps iteration anchored in the existing project instead of
starting over: discover, create, inspect, configure, check, run, observe, and
iterate back to inspect.

![Agent development lifecycle](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-adlc-en.svg)

| Stage | Local command or project surface |
| --- | --- |
| Discover | `agentseek create --list-templates` finds templates by goal. |
| Create | `agentseek create` renders an editable project. |
| Inspect | `agentseek info` shows its declared entry points and topology. |
| Configure | `.env` and project configuration provide runtime credentials and choices. |
| Check | `agentseek doctor` validates local readiness. |
| Run | `agentseek dev` starts the template-owned local stack. |
| Observe | `agentseek doctor --live` and lifecycle signals show its current state. |
| Iterate | Change the generated project, then return to **Inspect**. |

## Observability throughout the loop

Lifecycle diagnostics answer whether the declared project is ready and running:
`agentseek info` shows topology, `agentseek doctor` performs preflight checks,
and `agentseek doctor --live` checks declared services after startup. For
Desktop, scripts, and other machine consumers, use the versioned JSON contract
instead of parsing human output.

```bash
agentseek info --json
agentseek doctor --json
agentseek doctor --live --json
AGENTSEEK_CONSOLE=true agentseek doctor --live
```

`info --json` contains normalized services, references, and safe actions such
as which URL can be opened directly. It never includes environment values or
raw process or task commands. `AGENTSEEK_CONSOLE=true` enables local CLI spans
and lifecycle events. Optional LangSmith tracing, configured through the
settings already present in `deepagents/research`, answers what the agent did
inside an individual run.

<a id="guided-templates"></a>

## Guided templates

Choose by goal, then inspect a specific template before creating it. AgentSeek
maintains many templates without requiring you to memorize a catalog dump.

```bash
agentseek create --list-templates
agentseek create --list-templates --filter deepagents
agentseek create deepagents/research --describe
```

## Core concepts and commands

| Concept | What it provides |
| --- | --- |
| Template | A complete, editable application scaffold with its chosen runtime. |
| Lifecycle file | The project-owned declaration of paths, environment checks, services, processes, and tasks. |
| AgentSeek CLI | A consistent local interface for the declared lifecycle. |

| Command | Purpose |
| --- | --- |
| `create` | Render an application template. |
| `info` | Show declared entry points and lifecycle metadata. |
| `task` | Run a project-defined setup task. |
| `doctor` | Check local readiness or live declared-service health. |
| `dev` | Run the local development stack. |

## Documentation

- [Documentation home](https://ob-labs.github.io/agentseek/)
- [Get started](https://ob-labs.github.io/agentseek/get-started/)
- [Guides](https://ob-labs.github.io/agentseek/guides/)
- [Reference](https://ob-labs.github.io/agentseek/reference/)
- [Concepts](https://ob-labs.github.io/agentseek/concepts/)

<a id="community"></a>

## 🌐 Next Steps & Community

Explore **Deep Agents in Action**, a free LangChain / DeepAgents course with
AgentSeek labs, in the [course repository](https://github.com/datawhalechina/deepagents-in-action/).
Read the [documentation](https://ob-labs.github.io/agentseek/), join
[GitHub Discussions](https://github.com/ob-labs/agentseek/discussions),
[browse or report an issue](https://github.com/ob-labs/agentseek/issues), or
follow the [contribution guide](https://github.com/ob-labs/agentseek/blob/HEAD/CONTRIBUTING.md).

<div align="center">
  <a href="https://github.com/ob-labs/agentseek/discussions"><img alt="GitHub Discussions" src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" /></a>
  <a href="https://github.com/ob-labs/agentseek/blob/HEAD/CONTRIBUTING.md"><img alt="Contribute to AgentSeek" src="https://img.shields.io/badge/Contribute-AgentSeek-0ea5e9?style=for-the-badge" /></a>
</div>

---

<a id="development"></a>

## 🛠️ Development

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
make install
make check
make test
make docs-test
```

### Contributing

Contributions, fixes, and template improvements are welcome.

<div align="center">
  <a href="https://github.com/ob-labs/agentseek/graphs/contributors"><img alt="AgentSeek contributors" src="https://contrib.rocks/image?repo=ob-labs/agentseek&max=400" /></a>
</div>

---

## 📄 License

[Apache-2.0](https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE)
