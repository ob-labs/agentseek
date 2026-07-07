# {{ cookiecutter.project_name }}

Agentic hybrid RAG over an image-backed knowledge base.

## Quick Start

```bash
cp .env.example .env
uv sync --extra dev
npm install --prefix frontend
agentseek task seekdb
agentseek task ingest-sample
uv run hybrid-demo
agentseek dev
```

Open the frontend and try the Lab tab before using the chat. The Lab tab indexes a starter image pack and shows vector, sparse-token, exact full-text, metadata, and fused results side by side so you can see when each route helps.

## What This Template Teaches

- Vector search finds visually or semantically similar records.
- Sparse/keyword search rewards important words in captions.
- Full-text search is best for exact labels and names.
- Metadata search rewards file names, tags, and source metadata.
- Hybrid search fuses the routes so mixed queries do not depend on one retrieval strategy.
- Agent middleware teaches the model when to choose `semantic`, `keyword`, `exact`, or `balanced`.
- LangGraph custom routes expose upload, image serving, and compare-mode diagnostics on the same dev server as the graph.
- The frontend Lab tab ships with a starter image pack, guided cases, and visual rank comparisons so developers can test hybrid behavior immediately.

## First 10 Minutes

1. Start `agentseek dev`.
2. Open the Lab tab and click `Index starter pack`.
3. Run `uv run hybrid-demo`.
4. Run each guided case in the Lab tab and inspect the top hit per mode.
5. Open Compare Mode and try the prompts in `docs/hybrid-search-guide.md`.
6. Switch to Chat and ask the agent to choose the right mode.

## LangGraph Custom Routes

The template mounts a FastAPI app into `langgraph dev` through `langgraph.json` `http.app`. These custom routes handle built-in sample pack ingestion, archive upload, image thumbnail serving, and compare-mode diagnostics on the same `http://127.0.0.1:2024` origin as the agent. This keeps local filesystem paths out of the browser while avoiding an extra sidecar API process.

## Understand Hybrid Search

Run:

```bash
uv run ingest-images
uv run hybrid-demo
```

The default ingest command loads `examples/sample_pack/images`. The demo runs the same query through `semantic`, `keyword`, `exact`, and `balanced` modes. Use this before changing weights; it shows which route retrieved each result and why the fused rank changed.

## Design Notes

The first implementation uses caption token recall for sparse/keyword behavior and a bounded metadata candidate scan for filenames/tags so the demo works on the same pyseekdb surface as image vector search. If your installed `langchain-oceanbase` version supports `include_sparse=True` and `advanced_hybrid_search` for your document schema, you can replace the fallback sparse route with native sparse vectors.
