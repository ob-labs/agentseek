# DeepAgents — RAGFlow knowledge Q&A template

Scaffolds a DeepAgents knowledge-base application that connects to a
user-provided RAGFlow endpoint. Retrieval is dataset-scoped; document upload
and asynchronous parsing require an explicit LangGraph interrupt approval.

## Inputs

| Variable | Description | Default |
| --- | --- | --- |
| `project_name` | Human-readable project name. | `RAGFlow Knowledge QA DeepAgent` |
| `project_slug` | Generated Python package and directory name. | Derived from `project_name` |
| `author` | Project author. | `Your Name` |
| `system_prompt` | Safety and response-language instructions. | RAGFlow Q&A prompt |
| `default_model` | OpenAI-compatible model id. | Empty; configure at runtime |
| `langgraph_port` | Local LangGraph port. | `2024` |
| `frontend_port` | Local Vite port. | `5174` |

Runtime-only RAGFlow credentials, model credentials, upload-root location, and
LangSmith settings live in the generated `.env.example`.

## Generated layout

```text
{{ project_slug }}/
  .agentseek/lifecycle.toml
  .env.example
  README.md
  pyproject.toml
  langgraph.json
  src/{{ project_slug }}/
    __init__.py
    agent.py
    prompts.py
    ragflow.py
    tools.py
  frontend/
    package.json
    src/
```

## Contributor notes

- The template pins `ragflow-sdk==0.26.4`, which requires Python 3.13.
- The browser never receives the RAGFlow API key.
- Mutation tools are root-agent-only; delegated knowledge research is
  read-only.
- ContextSeek and browser file ingress are intentionally deferred.
