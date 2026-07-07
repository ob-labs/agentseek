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

The generated project includes `examples/sample_pack/`, a 26-image photo-style pack with known captions, tags, and visible text rendered into the image pixels.

The pack is intentionally kept in the generated project source tree so it is easy to inspect, edit, zip, and upload. It is not installed as Python package data; run the demo commands from the generated project root.

Mutable runtime state is intentionally separate: `SEEKDB_PATH` and `MEDIA_DATA_DIR` default to `~/.agentseek/hybrid-rag/{{ cookiecutter.project_slug }}/...`. Keeping embedded SeekDB files and upload indexes outside the project avoids `langgraph dev` hot reloads while a custom route is indexing images.

1. Balanced: `animal outdoors brown fur`
2. Keyword: `red product tea label`
3. Exact: `golden dog park`
4. Keyword: `blue logo`
5. Balanced: `fragile shipping label A17`
6. Exact: `paper invoice with red overdue stamp`
7. Semantic: `recycle glass bottle`
8. Balanced: `yellow warning triangle`

The pack intentionally includes near misses: a brown fur coat that matches the words but is not an animal, a yellow dog that looks similar but does not say `golden retriever`, a green tea label that looks like the red label package, a blue logo mug that matches the logo words but is not a shoe, a plain shipping box without `FRAGILE A17`, a receipt/calendar/stamp trio around the invoice terms, a recycling poster that says `GLASS BOTTLE`, and yellow safety-adjacent objects that are not triangular warning signs. Sample ingest embeds the PNG files with the multimodal image embedding path, while compare mode embeds the typed query with the text embedding path.

Run:

```bash
uv run ingest-images
uv run hybrid-demo
```

Then start `agentseek dev` and open the Lab tab. The Lab tab lets you index the starter pack, select each guided case, download the pack, and compare how the same query ranks across `semantic`, `keyword`, `exact`, and `balanced`.
