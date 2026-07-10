# {{ cookiecutter.project_name }}

DeepAgents knowledge-base Q&A backed by a user-provided RAGFlow service. The
LangGraph backend can list datasets, retrieve scoped chunks, and request human
approval before uploading or parsing documents. The React frontend streams
messages, tool calls, todos, and approval prompts.

## Prerequisites

- Python 3.13, `uv`, Node.js, and npm.
- A running RAGFlow service and API key. Configuring RAGFlow with
  `DOC_ENGINE=seekdb` is the recommended deployment.
- An OpenAI-compatible model and API key for the DeepAgents orchestrator.

## Quickstart

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

agentseek task sync
agentseek task frontend
agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek dev
```

The backend defaults to `http://127.0.0.1:{{ cookiecutter.langgraph_port }}` and
the frontend to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`. For remote
development, set `LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0` only on a
trusted network. Set `VITE_LANGGRAPH_API_URL` when the browser cannot reach the
backend through the page hostname.

```bash
LANGGRAPH_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 agentseek dev
```

## Configuration

`AGENTSEEK_MODEL`, `AGENTSEEK_API_KEY`, and optional `AGENTSEEK_API_BASE`
configure the DeepAgents model. They are independent of the models configured
inside RAGFlow.

`RAGFLOW_BASE_URL` and `RAGFLOW_API_KEY` connect to RAGFlow.
`RAGFLOW_UPLOAD_ROOT` is the only server-local directory from which the agent
may read upload candidates. Browser file upload is not included.

## Knowledge ingestion

The generated project includes `uploads/sample-policy.md`. Ask the agent to
upload that relative filename to an explicit dataset ID. The agent pauses
before calling RAGFlow and displays the dataset and filename. Approve or cancel
in the UI. Parsing uses the same approval flow and starts asynchronously.

Try retrieval with:

```text
List my RAGFlow datasets. Then search dataset <dataset-id> for the deployment policy.
```

Retrieved chunks are treated as untrusted data rather than agent instructions.
Dataset IDs are always explicit; the agent never searches every visible
dataset by default.

## Observability

Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and optionally
`LANGSMITH_PROJECT` to send traces to LangSmith. No other observability backend
is configured.

## Deferred capabilities

ContextSeek is not included in this version. End-user authentication,
browser-based file upload, and interrupt-edit-resume of retrieval strategies
are also outside the template scope. RAGFlow access is limited by the single
configured API key.

## Deviations from the template contract

The generated project requires Python `>=3.13,<3.14` because
`ragflow-sdk==0.26.4` declares that interpreter range. The focused template
tests verify the pinned SDK surface used by the adapter.
