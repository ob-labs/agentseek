# AgentSeek

AgentSeek is being redesigned.

This repository temporarily keeps only the smallest usable surface so the next
runtime and template design can stay focused. The old documentation, examples,
and most templates have been removed during the redesign.

## Current Entry Point

```bash
uvx agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
uvx agentseek doctor
uvx agentseek dev
uvx agentseek info
uvx agentseek task --list
```
