# Skills

Curated skills for agent-assisted development with AgentSeek templates.

AgentSeek-compatible template projects use `.agentseek/lifecycle.toml` as the
runtime contract. A template's `.env` file is only a source for declared
lifecycle environment checks; it is not automatically injected into child
processes. `agentseek dev --skip-check` skips the preliminary strict `doctor`
pass, while core required lifecycle inputs still apply.

## Install

### Via `agentseek` CLI (recommended)

The `agentseek skills` subcommand defaults to this repo — no need to type the source:

```bash
# All skills, globally
agentseek skills add --all --global

# Specific skill
agentseek skills add --skill langsmith-trace --global --yes

# Specific agent
agentseek skills add --all --global --agent claude-code
```

### Via `npx skills` directly

```bash
npx skills add ob-labs/agentseek --all --global
npx skills add ob-labs/agentseek --skill langsmith-trace --global --yes
```

### Project-local (for shared repos)

```bash
agentseek skills add --all
```

Omit `--global` to install into the current project only.

### Standalone copies (CI / airgapped)

```bash
agentseek skills add --all --global --copy
```

## Available Skills

| Skill | Purpose |
|-------|---------|
| `langsmith-trace` | LangSmith CLI setup, tracing, and trace debugging for AgentSeek backends |
| `langchain-dev-guide` | LangChain / LangGraph / DeepAgents pitfalls and fixes, plus CN model integration (DeepSeek, Qwen, GLM) |
| `github-repo-cards` | Generate visual repo cards for documentation and social sharing |

## Update & Remove

```bash
agentseek skills update           # update all
agentseek skills remove           # interactive remove
npx skills update -g              # update global (alternative)
npx skills remove --all --global  # remove everything
```
