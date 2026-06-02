# Skills

This directory contains a curated collection of skills designed to address tasks across various fields.

By default, these skills are not included in the agentseek release.

## Install

Install all skills to all detected agents at once:

```bash
npx skills add ob-labs/agentseek --all
```

Or pick specific skills and agents:

```bash
npx skills add ob-labs/agentseek --skill github-repo-cards --agent claude-code
npx skills add ob-labs/agentseek --skill langchain-cn-models --agent claude-code
npx skills add ob-labs/agentseek --skill langchain-dev-guide --agent claude-code
```

To verify what was installed:

```bash
npx skills list
```

To remove installed skills:

```bash
npx skills remove
```
