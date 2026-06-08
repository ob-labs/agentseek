# User Query Convention

A cross-platform convention for skill authors to define structured questions. Agents parse these blocks and render them via the best available tool on their platform.

## Block Types

### `<!-- query -->` — Single or multi-choice question

Use when the user must pick between approaches, modes, or options.

```markdown
<!-- query
type: choice
question: "Which approach do you prefer?"
options:
  - label: "Code generation"
    description: "Generate integration class in your repo"
  - label: "Third-party library"
    description: "Use langchain-dev-utils built-in adapters"
default: 1
-->
```

Fields:
- `type`: `choice` (single-select) or `multi-choice` (multi-select)
- `question`: The question to present
- `options`: 2–4 options, each with `label` and `description`
- `default`: 1-based index of the default option (applied when user says "use defaults" or doesn't answer)

### `<!-- gather -->` — Collect multiple inputs

Use when the skill needs several pieces of information from the user before proceeding.

```markdown
<!-- gather
prompt: "Confirm the following details:"
fields:
  - name: model_name
    question: "Model name (lowercase)"
    example: "qwen"
    required: true
  - name: api_base
    question: "API base URL"
    example: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    required: true
  - name: api_key_env
    question: "API key env var name"
    example: "QWEN_API_KEY"
    required: true
fallback: "Use reasonable defaults from the provider's documentation."
-->
```

Fields:
- `prompt`: Introductory text shown before the questions
- `fields`: List of inputs to collect; each has `name`, `question`, `example`, and optional `required` (default true)
- `fallback`: Instruction for the agent when the user declines to answer or says "just use defaults"

## Platform Rendering

| Platform | `<!-- query -->` | `<!-- gather -->` |
|----------|-----------------|-------------------|
| Claude Code | `AskUserQuestion` with `options` | `AskUserQuestion` with one question per field |
| Gemini CLI | `ask_user` | `ask_user` per field |
| Copilot CLI | Output as formatted text with numbered options, wait for reply | Output as numbered list with examples, wait for reply |
| Cursor / Windsurf | Output as formatted text, wait for reply | Output as formatted text, wait for reply |
| Codex | Output as formatted text (autonomous mode — apply defaults if no response) | Apply defaults (autonomous mode) |

### Claude Code example rendering

For a `<!-- query -->` block, the agent calls:
```
AskUserQuestion({
  questions: [{
    question: "Which approach do you prefer?",
    header: "Approach",
    options: [
      { label: "Code generation", description: "Generate integration class in your repo" },
      { label: "Third-party library", description: "Use langchain-dev-utils built-in adapters" }
    ],
    multiSelect: false
  }]
})
```

For a `<!-- gather -->` block, the agent calls `AskUserQuestion` with up to 4 questions (the tool's limit), batching if needed.

### Fallback text rendering (Cursor, Copilot, Codex)

For platforms without structured prompting, output:

```
**Which approach do you prefer?**

1. **Code generation** — Generate integration class in your repo
2. **Third-party library** — Use langchain-dev-utils built-in adapters

(Reply with number or description. Default: 1)
```

## Guidelines for Skill Authors

1. **Place blocks inline** where the question naturally occurs in the skill flow — not in a separate section
2. **Always provide a `default` or `fallback`** — agents running in autonomous mode need a way to proceed without blocking
3. **Keep options to 2–4** — matches `AskUserQuestion` limits and avoids decision fatigue
4. **Use `<!-- gather -->` sparingly** — prefer inferring from project context (package manager, existing config) over asking
5. **Blocks are HTML comments** — they don't render in markdown viewers, so the surrounding prose should still make sense without them
6. **Prose context around blocks is required** — the block is for the agent's structured rendering; the surrounding markdown provides context for human readers browsing the skill file
