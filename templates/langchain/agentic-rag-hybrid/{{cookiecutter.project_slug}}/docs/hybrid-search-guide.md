# Hybrid Search Guide

Hybrid search is useful when one retrieval route is not enough.

## Modes

| Mode | Weights | Use When |
| --- | --- | --- |
| semantic | V 70 / S 20 / F 10 | The query is conceptual or visual. |
| keyword | V 20 / S 60 / F 20 | The query contains important labels, colors, brands, or object terms. |
| exact | V 10 / S 20 / F 70 | The query asks for an exact caption term, filename, label, or category. |
| balanced | V 40 / S 30 / F 30 | The query mixes visual similarity and words. |

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

