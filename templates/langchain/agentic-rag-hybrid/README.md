# langchain/agentic-rag-hybrid

Cookiecutter template for a LangChain/LangGraph hybrid RAG application over an image-backed knowledge base.

Use this template when you want developers to compare vector, sparse-token, exact full-text, metadata, and fused hybrid retrieval against the same indexed image pack. The generated app includes a guided React lab, LangGraph chat agent, LangGraph custom routes, embedded OceanBase seekdb storage through `langchain-oceanbase`, SiliconFlow-compatible chat/embedding/VLM defaults, and optional Phoenix observability.

## Architecture

- LangGraph runs the `hybrid-rag` assistant and mounts FastAPI custom routes from `langgraph.json`.
- `langchain-oceanbase` `OceanbaseVectorStore` stores image vectors and document fields in embedded OceanBase seekdb mode.
- Hybrid retrieval keeps vector, sparse, full-text, and metadata scores visible so developers can inspect mode effects.
- The React frontend exposes Guided Lab, Compare Modes, and Ask Agent tabs against the same backend origin.
- Phoenix tracing is optional and uses the AgentSeek Phoenix image with OceanBase seekdb trace storage.

## Cookiecutter Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `project_name` | `My Hybrid RAG Agent` | Human-readable generated project name. |
| `project_slug` | Derived from `project_name` | Python package and directory name. |
| `author` | `Your Name` | Generated project metadata. |
| `system_prompt` | Hybrid retrieval guidance | Agent instruction for choosing search modes. |
| `default_model_provider` | `openai` | LangChain chat provider adapter. |
| `default_model` | `openai:zai-org/GLM-5.2` | Default hosted chat model. |
| `seekdb_path` | `~/.agentseek/hybrid-rag/<slug>/seekdb` | Embedded seekdb data directory outside the project tree. |
| `seekdb_db_name` | `test` | Embedded seekdb database name. |
| `image_table_name` | `hybrid_image_documents` | Image document table/collection name. |
| `media_data_dir` | `~/.agentseek/hybrid-rag/<slug>/media` | Runtime media directory outside the project tree. |
| `embedding_model` | `Qwen/Qwen3-VL-Embedding-8B` | SiliconFlow-compatible multimodal embedding model. |
| `embedding_dimension` | `1024` | Expected embedding dimension. |
| `vlm_model` | `zai-org/GLM-4.5V` | Optional VLM captioning model. |
| `frontend_port` | `5175` | Vite development server port. |

Runtime-only secrets and endpoints belong in the generated `.env`, not in Cookiecutter prompts.

## Generated Layout

```text
{{cookiecutter.project_slug}}/
  .agentseek/lifecycle.toml
  .env.example
  README.md
  docker-compose.yml
  langgraph.json
  docs/hybrid-search-guide.md
  examples/sample_pack/
  frontend/
  src/{{cookiecutter.project_slug}}/
  tests/
```

## Contributor Notes

- Keep generated setup instructions on lifecycle tasks: `agentseek task sync`, `agentseek task frontend`, `agentseek task seekdb`, and `agentseek task ingest-sample`.
- Use canonical `AGENTSEEK_MODEL_PROVIDER`, `AGENTSEEK_MODEL`, `AGENTSEEK_API_KEY`, and `AGENTSEEK_API_BASE` as the public model configuration. Provider-native names may remain compatibility aliases.
- Keep backend and frontend servers loopback-only by default. Remote development must use `LANGGRAPH_HOST` and `FRONTEND_HOST` overrides, while the browser frontend derives backend URLs from `window.location.hostname`.
- Keep mutable seekdb and media paths outside the generated project tree so `langgraph dev` does not reload while indexing files.
- Update the focused smoke workflow when changes affect real seekdb ingestion, SiliconFlow embeddings, Phoenix tracing, or frontend compare behavior.
