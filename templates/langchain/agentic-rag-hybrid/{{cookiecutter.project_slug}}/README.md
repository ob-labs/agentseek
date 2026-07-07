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

Open the frontend and try the Lab tab before using the chat. The Lab tab indexes a richer photo-style starter image pack with animal, product, shipping, document, bottle, and safety-sign near misses. It shows vector, sparse-token, exact full-text, metadata, and fused results side by side so you can see when each route helps.

`agentseek task seekdb` prepares the embedded SeekDB data directory. The template uses `langchain-oceanbase` `OceanbaseVectorStore` for storage and search; it does not call `pyseekdb` collections directly. By default, `SEEKDB_PATH` and `MEDIA_DATA_DIR` live under `~/.agentseek/hybrid-rag/{{ cookiecutter.project_slug }}/` so LangGraph dev does not reload while DB/index/upload files are changing.

The starter pack is a source-tree demo fixture under `examples/sample_pack/`, not Python package data. Keep the generated project directory intact when running `agentseek dev`, `uv run ingest-images`, `uv run hybrid-demo`, or the sample-pack custom routes.

## SiliconFlow Models

The template uses SiliconFlow for agent chat, image/text retrieval embeddings, and optional VLM captioning by default:

- `AGENTSEEK_MODEL={{ cookiecutter.default_model }}` through the SiliconFlow OpenAI-compatible chat endpoint
- `EMBEDDING_MODEL={{ cookiecutter.embedding_model }}` through the SiliconFlow embeddings endpoint
- `VLM_MODEL={{ cookiecutter.vlm_model }}` through the SiliconFlow OpenAI-compatible chat endpoint

Set `SILICONFLOW_API_KEY` once in `.env` to feed all three paths. Use `OPENAI_API_KEY`, `EMBEDDING_API_KEY`, or `VLM_API_KEY` only when you need separate credentials for one path.

## What This Template Teaches

- Vector search finds visually or semantically similar records.
- Sparse/keyword search rewards important words in captions.
- Full-text search is best for exact labels and names.
- Metadata search rewards file names, tags, and source metadata.
- Hybrid search fuses the routes so mixed queries do not depend on one retrieval strategy.
- Agent middleware teaches the model when to choose `semantic`, `keyword`, `exact`, or `balanced`.
- LangGraph custom routes expose upload, image serving, and compare-mode diagnostics on the same dev server as the graph.
- The frontend Lab tab ships with photo-style fixtures, visible in-image text, guided cases, and visual rank comparisons so developers can test hybrid behavior immediately.

## First 10 Minutes

1. Start `agentseek dev`.
2. Open the Lab tab and click `Index starter pack`.
3. Run `uv run hybrid-demo`.
4. Select each guided case in the Lab tab and inspect the top hit per mode.
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

The default ingest command loads `examples/sample_pack/images`, stages each caption through a LangChain `Embeddings` adapter, embeds the PNG files through the SiliconFlow multimodal image embedding path, and writes records through `OceanbaseVectorStore` in embedded SeekDB mode. The demo embeds each query through the SiliconFlow text embedding path, then runs the same query through `semantic`, `keyword`, `exact`, and `balanced` modes. Use this before changing weights; it shows which route retrieved each result and why the fused rank changed.

## Design Notes

The implementation uses `langchain-oceanbase` as the storage/search infrastructure. Image vectors, hashed sparse token vectors, full-text content, captions, tags, and metadata are written through `OceanbaseVectorStore` with embedded SeekDB enabled by `SEEKDB_PATH`. The app intentionally keeps vector, sparse, full-text, and metadata routes visible in the Lab tab so developers can see how each retrieval signal changes the fused rank.
