# agentseek docs style guide

This is an internal guide for anyone editing files under `docs/`. It is not part of
the published site (the directory `docs/_data/` is excluded from the MkDocs nav).
Keep it short — when it gets long, the docs themselves have probably drifted.

## 1. Product framing

agentseek is an **Agent Harness**. The stable framing is **two packages, split
by job**:

- **`agentseek-cli`** — the project lifecycle CLI. It owns `create / run /
  build / deploy / api / ctx / skills` and is installable on its own via
  `uv tool install agentseek-cli`.
- **`agentseek`** — the harness itself. It owns the runtime CLI (`chat /
  gateway / install / update / …`) plus the library surface you embed. It is
  resolved through `uv sync` in this repo or inside a generated project, not by
  `pip install agentseek`.

When you write a new page, surface the job split early. If a page uses a repo
checkout where both packages are present, say that the visible `agentseek`
command is the **merged surface** rather than pretending one package owns every
command.

## 2. Tone by quadrant

We mix tones on purpose. Match the quadrant, not your mood.

| Quadrant       | Reference style                | What that means here                                                                                            |
| -------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Tutorials      | LangChain, LanceDB             | Friendly, second-person, occasional first-person plural. Show the command, then the output, then the takeaway. |
| Blog           | LangChain, LanceDB             | Same as tutorials. A narrator voice is welcome.                                                                 |
| How-to         | Google Cloud, TiDB             | Tight, task-first. Open with "Use this when…", then prerequisites, then numbered steps.                        |
| Reference      | Google Cloud, TiDB             | Neutral and scannable. Tables, lists, exact strings. No narration.                                              |
| Explanation    | Google Cloud, TiDB (relaxed)   | Discuss trade-offs and history. Allow a sentence of opinion when it earns its place.                           |

## 3. Person & voice

- Default to **you / 你**. Address the reader directly.
- **we / 我们** is allowed in any quadrant, but use it sparingly to mean "the
  project / the maintainers". Never use it to mean "you and I together".
- Banned filler: *let's*, *let us*, *together we*, *as we all know*,
  *让我们一起*, *众所周知*, *不难发现*, *相信你*, *轻而易举*.
- Banned marketing words: *blazing*, *seamless*, *revolutionary*, *world-class*,
  *cutting-edge*, *powerful*, *amazing*, *awesome*, *elegant*,
  *极速*, *革命性*, *业界领先*, *完美*, *强大的*, *无缝*, *一键搞定*.

## 4. Mechanics

- Lead with verbs in imperative ("Run", "Set", "Install", "运行", "设置", "安装").
- Keep paragraphs short. Three-to-five sentences is plenty.
- Use fenced code blocks with explicit language tags. Show input *and* expected
  output when the output is short and stable.
- For Chinese pages: full-width punctuation in prose, half-width inside code,
  commands, file paths, version numbers, and identifiers.
- Reference file locations as `path/to/file.py:LINE` so editors can jump.
- Cross-link with relative paths inside `docs/`. Never write `../docs/...` or
  `/docs/...`.

## 5. Lifecycle CLI ↔ harness runtime

Whenever a page demonstrates a workflow that exists on both paths, prefer the
pattern:

```text
1. Describe the goal in one sentence.
2. Show the harness API call (Python) or runtime CLI form.
3. Show the equivalent project lifecycle command only if the same outcome is
   actually reachable through `agentseek-cli`.
4. Point at the relevant reference page for flags / env vars.
```

If only one path is appropriate (for example, `build` / `deploy` belong to
`agentseek-cli`; subclassing a hook belongs to the harness), say so explicitly
instead of silently dropping the other.

## 6. Front-matter

Every published page keeps the existing keys: `title`, `type`, `audience`,
`runs`, `verified_on`, `sources`. `type` must be one of `tutorial`, `how-to`,
`reference`, `explanation`, `blog`. `verified_on` is the date the commands on
the page were last run end-to-end.
