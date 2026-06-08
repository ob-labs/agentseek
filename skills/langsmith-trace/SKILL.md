---
name: langsmith-trace
description: "LangSmith tracing and trace debugging for AgentSeek templates. Covers CLI installation, adding tracing to LangGraph apps, querying traces, and inspecting run IO. Use when debugging agent backends, investigating slow traces, or adding observability to a template."
---

# LangSmith Trace

Add tracing to your agent and query traces for debugging. Supports Python and TypeScript.

> [!IMPORTANT]
> This skill is tuned for AgentSeek template backends (LangGraph + middleware stacks). For general LangSmith concepts, see the upstream [langsmith-skills](https://github.com/langchain-ai/langsmith-skills) repo.

## Installation & Setup

### 1. Install the CLI

```bash
curl -sSL https://raw.githubusercontent.com/langchain-ai/langsmith-cli/main/scripts/install.sh | sh
```

The binary installs to `~/.local/bin/langsmith`. If `langsmith` is not found after install, add to your shell profile:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Set your API key

Add to `~/.zshrc` (or the template's `.env` file):

```bash
export LANGSMITH_API_KEY=lsv2_pt_your_key_here
```

Key format must start with `lsv2_pt_`. Get yours at https://smith.langchain.com/settings.

### 3. Verify

```bash
langsmith project list
```

If you see a JSON array of projects, you're set. Common failures:
- **`command not found`** — `~/.local/bin` not in PATH (see step 1)
- **401 Unauthorized** — key is wrong or expired; regenerate at LangSmith settings
- **Empty array `[]`** — valid auth but no projects yet; create one in the UI or run a traced app

## Adding Tracing

### LangGraph / LangChain apps (automatic)

Just set environment variables — no code changes needed:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=lsv2_pt_...
export LANGSMITH_PROJECT=my-project  # optional, defaults to "default"
```

For serverless (Python): also set `LANGCHAIN_CALLBACKS_BACKGROUND=false` to ensure traces flush before function exit.

### Non-LangChain apps

Use the `@traceable` decorator (Python) or `traceable()` wrapper (TypeScript) and wrap your LLM client:

```python
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

client = wrap_openai(OpenAI())

@traceable
def my_pipeline(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
    )
    return resp.choices[0].message.content
```

```typescript
import { traceable } from "langsmith/traceable";
import { wrapOpenAI } from "langsmith/wrappers";
import OpenAI from "openai";

const client = wrapOpenAI(new OpenAI());

const myPipeline = traceable(async (question: string) => {
  const resp = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: question }],
  });
  return resp.choices[0].message.content || "";
}, { name: "my_pipeline" });
```

## Debugging a Trace (Step-by-Step)

This is the recommended workflow for investigating agent behavior:

### Step 1: Find the right project

```bash
langsmith project list
```

Look at `last_run_start_time` to find which project has recent activity. Don't assume — LangGraph apps default to the `"default"` project, not a named one.

### Step 2: List recent traces

```bash
langsmith trace list --project default --limit 5

# Or with full hierarchy inline (combines steps 2+3):
langsmith trace list --project default --limit 5 --show-hierarchy
```

### Step 3: Get the trace hierarchy

```bash
langsmith trace get <trace-id> --project <name>
```

This returns the full run tree — use it to understand the agent's execution flow.

### Step 4: Get IO for all runs in a trace

```bash
langsmith run list --trace-ids <trace-id> --project <name> --include-io
```

This gives you inputs and outputs for every run (LLM calls, tool calls, middleware).

### Step 5: Drill into a specific run

```bash
langsmith run get <run-id> --include-io
```

## AgentSeek Trace Structure

Our templates produce traces with this typical hierarchy:

```
<agent_name> (root chain)
├── SkillsMiddleware.before_agent
├── PatchToolCallsMiddleware.before_agent
├── MemoryMiddleware.before_agent
├── model (chain) ← LLM turn
│   ├── TodoListMiddleware.awrap_model_call
│   ├── SkillsMiddleware.awrap_model_call
│   ├── FilesystemMiddleware.awrap_model_call
│   ├── SubAgentMiddleware.awrap_model_call
│   ├── SummarizationMiddleware.awrap_model_call
│   ├── AnthropicPromptCachingMiddleware.awrap_model_call
│   ├── MemoryMiddleware.awrap_model_call
│   └── ChatOpenAI (llm) ← actual LLM call (inputs/outputs here)
├── TodoListMiddleware.after_model
├── tools (chain) ← tool execution
│   ├── FilesystemMiddleware.awrap_tool_call
│   └── <tool_name> (tool) ← actual tool (inputs/outputs here)
├── model (chain) ← next LLM turn
│   └── ... (same middleware stack)
└── TodoListMiddleware.after_model
```

Key points:
- The **actual LLM call** is always the innermost `ChatOpenAI` run
- **Tool results** are in the `<tool_name>` run (e.g., `generate_cover`, `execute`)
- Middleware wrappers are transparent — they add latency but the IO you care about is at the leaf nodes

## Gotchas

### `--full` vs `--include-io` on individual runs

**Problem:** `langsmith run get <id> --full` can return null for inputs/outputs, even though the data exists. Despite `--full` being documented as equivalent to `--include-metadata --include-io --include-feedback`, the underlying API behavior differs for individual run fetches in some CLI versions.

**Solution:** Always use `--include-io` explicitly when inspecting specific runs:
```bash
# DO THIS
langsmith run get <run-id> --include-io

# NOT THIS (may return null IO despite docs saying it includes --include-io)
langsmith run get <run-id> --full
```

`--full` works reliably on `trace export` and `run list`, but has inconsistent behavior on individual `run get` calls. If this is fixed in a future CLI version, `--include-io` still works correctly — it's always safe.

### Null IO even with `--include-io`

If inputs/outputs come back null even with `--include-io`, the project has IO logging disabled. Check for these environment variables in the template's `.env`:

```bash
LANGCHAIN_HIDE_INPUTS=true    # hides inputs from traces
LANGCHAIN_HIDE_OUTPUTS=true   # hides outputs from traces
```

Remove or set to `false` to enable IO capture for debugging.

### Project confusion

LangGraph apps trace to the `"default"` project unless `LANGSMITH_PROJECT` is explicitly set. Always run `langsmith project list` first and check `last_run_start_time` to find where your traces actually landed.

### Tips

- Add `--format pretty` for human-readable output during interactive debugging
- Use `LANGSMITH_ENDPOINT` env var if connecting to a self-hosted LangSmith instance
- The middleware ordering in the trace tree is configurable — your template may differ slightly from the diagram above

## CLI Reference

Full command reference: [reference/cli-commands.md](reference/cli-commands.md)
