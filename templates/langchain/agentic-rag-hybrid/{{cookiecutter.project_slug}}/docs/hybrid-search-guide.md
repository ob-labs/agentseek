# Hybrid Search Guide

Hybrid search is useful when one retrieval route is not enough.

## Modes

| Mode | Weights | Use When |
| --- | --- | --- |
| semantic | V 65 / S 15 / F 10 / M 10 | The query is conceptual or visual. |
| keyword | V 15 / S 45 / F 15 / M 25 | The query contains important labels, colors, brands, or object terms. |
| exact | V 10 / S 15 / F 55 / M 20 | The query asks for an exact caption term, filename, label, or category. |
| balanced | V 35 / S 25 / F 25 / M 15 | The query mixes visual similarity and words. |

V = vector similarity, S = sparse caption-token recall, F = exact full-text phrase recall, M = metadata/file-name recall.

## Cases To Try

The generated project includes `examples/sample_pack/`, a tiny image pack with known captions and tags.

1. Semantic: `outdoor animal with brown fur`
2. Keyword: `red product label`
3. Exact: `golden retriever`
4. Balanced: `similar shoes with visible blue logo`

Run:

```bash
uv run ingest-images
uv run hybrid-demo
```

Then start `agentseek dev` and open the Lab tab. The Lab tab lets you index the starter pack, run each guided case, download the pack, and compare how the same query ranks across `semantic`, `keyword`, `exact`, and `balanced`.
