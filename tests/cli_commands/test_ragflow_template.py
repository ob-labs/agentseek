"""Focused behavior tests for the rendered RAGFlow template."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates" / "deepagents" / "ragflow-knowledge-qa"


@pytest.fixture
def rendered_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Render the template and import its adapter/tool modules."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(template=str(TEMPLATE_ROOT), output_dir=str(out_dir), no_input=True)
    generated = next(path for path in out_dir.iterdir() if path.is_dir())
    monkeypatch.syspath_prepend(str(generated / "src"))

    package = generated.name
    modules: dict[str, ModuleType] = {}
    for leaf in ("ragflow", "tools"):
        name = f"{package}.{leaf}"
        sys.modules.pop(name, None)
        try:
            modules[leaf] = importlib.import_module(name)
        except ModuleNotFoundError:
            pytest.fail(f"rendered template is missing {leaf}.py")
    yield modules
    for leaf in ("ragflow", "tools"):
        sys.modules.pop(f"{package}.{leaf}", None)


def test_retrieve_requires_explicit_dataset_scope(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """Retrieval cannot silently expand to every dataset visible to the API key."""
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=object(), upload_root=tmp_path)

    with pytest.raises(ValueError, match="dataset_ids must contain at least one dataset ID"):
        adapter.retrieve(dataset_ids=[], question="Where is the policy?")


def test_retrieve_calls_ragflow_and_serializes_chunks(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """The adapter returns JSON-safe evidence instead of leaking SDK objects."""

    class Client:
        def __init__(self) -> None:
            self.request: dict[str, object] | None = None

        def retrieve(self, **kwargs: object) -> list[SimpleNamespace]:
            self.request = kwargs
            return [
                SimpleNamespace(
                    id="chunk-1",
                    content="Approved deployment policy",
                    dataset_id="dataset-1",
                    document_id="document-1",
                    document_name="policy.md",
                    similarity=0.91,
                )
            ]

    client = Client()
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=client, upload_root=tmp_path)

    result = adapter.retrieve(
        dataset_ids=["dataset-1"],
        question="Where is the policy?",
        max_chunks=5,
    )

    assert client.request == {
        "dataset_ids": ["dataset-1"],
        "question": "Where is the policy?",
        "page": 1,
        "page_size": 5,
        "similarity_threshold": 0.2,
        "vector_similarity_weight": 0.3,
        "top_k": 1024,
    }
    assert result == [
        {
            "id": "chunk-1",
            "content": "Approved deployment policy",
            "dataset_id": "dataset-1",
            "document_id": "document-1",
            "document_name": "policy.md",
            "similarity": 0.91,
        }
    ]


def test_list_datasets_returns_compact_scope_choices(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """Dataset discovery exposes selection metadata without raw SDK state."""

    class Client:
        def list_datasets(self, **kwargs: object) -> list[SimpleNamespace]:
            assert kwargs == {"page": 3, "page_size": 10}
            return [
                SimpleNamespace(
                    id="dataset-1",
                    name="Policies",
                    description="Deployment policies",
                    document_count=4,
                    chunk_count=16,
                )
            ]

    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=Client(), upload_root=tmp_path)

    assert adapter.list_datasets(page=3, page_size=10) == [
        {
            "id": "dataset-1",
            "name": "Policies",
            "description": "Deployment policies",
            "document_count": 4,
            "chunk_count": 16,
        }
    ]


@pytest.mark.parametrize(
    ("page", "page_size", "message"),
    [
        (0, 30, "page must be at least 1"),
        (1, 0, "page_size must be between 1 and 100"),
        (1, 101, "page_size must be between 1 and 100"),
    ],
)
def test_list_datasets_limits_pagination(
    rendered_modules: dict[str, ModuleType],
    tmp_path: Path,
    page: int,
    page_size: int,
    message: str,
) -> None:
    """Dataset discovery remains pageable without allowing unbounded responses."""
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=object(), upload_root=tmp_path)

    with pytest.raises(ValueError, match=message):
        adapter.list_datasets(page=page, page_size=page_size)


def test_list_datasets_tool_forwards_requested_page(
    rendered_modules: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The agent can discover dataset IDs beyond the first result page."""
    calls: list[dict[str, int]] = []

    class Adapter:
        def list_datasets(self, **kwargs: int) -> list[dict[str, object]]:
            calls.append(kwargs)
            return []

    tools = rendered_modules["tools"]
    monkeypatch.setattr(tools, "_adapter", lambda: Adapter())

    assert tools.list_ragflow_datasets.func(page=3, page_size=10) == []
    assert calls == [{"page": 3, "page_size": 10}]


def test_upload_rejects_paths_outside_staging_root(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """An agent-supplied path cannot escape the configured upload directory."""
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    (tmp_path / "secret.txt").write_text("not uploadable", encoding="utf-8")
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=object(), upload_root=upload_root)

    with pytest.raises(ValueError, match="must stay within RAGFLOW_UPLOAD_ROOT"):
        adapter.upload_documents(dataset_id="dataset-1", relative_paths=["../secret.txt"])


def test_upload_reads_staged_files_and_calls_dataset(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """Approved uploads send named byte payloads through the selected dataset."""

    class Dataset:
        def __init__(self) -> None:
            self.documents: list[dict[str, object]] | None = None

        def upload_documents(self, documents: list[dict[str, object]]) -> list[SimpleNamespace]:
            self.documents = documents
            return [SimpleNamespace(id="document-1", name="policy.md")]

    class Client:
        def __init__(self, dataset: Dataset) -> None:
            self.dataset = dataset

        def list_datasets(self, **kwargs: object) -> list[Dataset]:
            assert kwargs == {"id": "dataset-1"}
            return [self.dataset]

    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    (upload_root / "policy.md").write_bytes(b"approved policy")
    dataset = Dataset()
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(
        client=Client(dataset),
        upload_root=upload_root,
    )

    result = adapter.upload_documents(dataset_id="dataset-1", relative_paths=["policy.md"])

    assert dataset.documents == [{"display_name": "policy.md", "blob": b"approved policy"}]
    assert result == [{"id": "document-1", "name": "policy.md"}]


def test_parse_starts_non_blocking_ragflow_operation(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """Parsing uses async_parse_documents instead of polling inside an agent run."""

    class Dataset:
        def __init__(self) -> None:
            self.document_ids: list[str] | None = None

        def async_parse_documents(self, document_ids: list[str]) -> None:
            self.document_ids = document_ids

    class Client:
        def __init__(self, dataset: Dataset) -> None:
            self.dataset = dataset

        def list_datasets(self, **kwargs: object) -> list[Dataset]:
            assert kwargs == {"id": "dataset-1"}
            return [self.dataset]

    dataset = Dataset()
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(
        client=Client(dataset),
        upload_root=tmp_path,
    )

    result = adapter.parse_documents(
        dataset_id="dataset-1",
        document_ids=["document-1", "document-2"],
    )

    assert dataset.document_ids == ["document-1", "document-2"]
    assert result == {
        "status": "accepted",
        "dataset_id": "dataset-1",
        "document_ids": ["document-1", "document-2"],
    }


def test_parse_tool_cancel_never_calls_ragflow(
    rendered_modules: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A denied interrupt ends the tool call without a mutation."""

    class Adapter:
        def parse_documents(self, **kwargs: object) -> dict[str, object]:
            pytest.fail(f"parse should not run after cancellation: {kwargs}")

    tools = rendered_modules["tools"]
    monkeypatch.setattr(tools, "_adapter", lambda: Adapter())
    monkeypatch.setattr(tools, "interrupt", lambda payload: {"approved": False})

    result = tools.parse_ragflow_documents.func(
        dataset_id="dataset-1",
        document_ids=["document-1"],
    )

    assert result == {
        "status": "cancelled",
        "operation": "parse_documents",
        "dataset_id": "dataset-1",
    }


def test_parse_tool_approval_executes_reviewed_operation(
    rendered_modules: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The resumed tool executes only the dataset and documents shown for review."""
    calls: list[dict[str, object]] = []
    interrupts: list[dict[str, object]] = []

    class Adapter:
        def parse_documents(self, **kwargs: object) -> dict[str, object]:
            calls.append(kwargs)
            return {"status": "accepted", **kwargs}

    tools = rendered_modules["tools"]
    monkeypatch.setattr(tools, "_adapter", lambda: Adapter())

    def approve(payload: dict[str, object]) -> dict[str, bool]:
        interrupts.append(payload)
        return {"approved": True}

    monkeypatch.setattr(tools, "interrupt", approve)

    result = tools.parse_ragflow_documents.func(
        dataset_id="dataset-1",
        document_ids=["document-1", "document-2"],
    )

    assert interrupts == [
        {
            "kind": "ragflow_approval",
            "operation": "parse_documents",
            "dataset_id": "dataset-1",
            "document_ids": ["document-1", "document-2"],
            "count": 2,
        }
    ]
    assert calls == [
        {
            "dataset_id": "dataset-1",
            "document_ids": ["document-1", "document-2"],
        }
    ]
    assert result["status"] == "accepted"


def test_adapter_factory_lazily_builds_current_ragflow_sdk_client(
    rendered_modules: dict[str, ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Runtime configuration reaches the pinned SDK without importing it during render tests."""
    constructor_calls: list[dict[str, str]] = []

    class Client:
        pass

    def build_client(**kwargs: str) -> Client:
        constructor_calls.append(kwargs)
        return Client()

    monkeypatch.setitem(sys.modules, "ragflow_sdk", SimpleNamespace(RAGFlow=build_client))
    monkeypatch.setenv("RAGFLOW_BASE_URL", "http://ragflow.example:9380/")
    monkeypatch.setenv("RAGFLOW_API_KEY", "secret-key")
    monkeypatch.setenv("RAGFLOW_UPLOAD_ROOT", str(tmp_path / "uploads"))

    adapter = rendered_modules["ragflow"].RAGFlowAdapter.from_env()

    assert constructor_calls == [
        {
            "api_key": "secret-key",
            "base_url": "http://ragflow.example:9380",
        }
    ]
    assert isinstance(adapter.client, Client)
    assert adapter.upload_root == tmp_path / "uploads"


def test_upload_tool_rejects_empty_review_without_interrupting(
    rendered_modules: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The UI is not asked to approve an operation with no upload candidates."""
    tools = rendered_modules["tools"]
    monkeypatch.setattr(
        tools,
        "interrupt",
        lambda payload: pytest.fail(f"unexpected approval prompt: {payload}"),
    )

    with pytest.raises(ValueError, match="relative_paths must contain at least one staged file"):
        tools.upload_staged_documents.func(dataset_id="dataset-1", relative_paths=[])


def test_parse_tool_rejects_empty_review_without_interrupting(
    rendered_modules: dict[str, ModuleType], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The UI is not asked to approve parsing when no documents were selected."""
    tools = rendered_modules["tools"]
    monkeypatch.setattr(
        tools,
        "interrupt",
        lambda payload: pytest.fail(f"unexpected approval prompt: {payload}"),
    )

    with pytest.raises(ValueError, match="document_ids must contain at least one document ID"):
        tools.parse_ragflow_documents.func(dataset_id="dataset-1", document_ids=[])


def test_sdk_errors_do_not_leak_credentials(rendered_modules: dict[str, ModuleType], tmp_path: Path) -> None:
    """Tool-facing errors identify the operation without exposing SDK response details."""

    class Client:
        def retrieve(self, **kwargs: object) -> list[object]:
            error = RuntimeError("Authorization: Bearer secret-key")
            raise error

    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=Client(), upload_root=tmp_path)

    with pytest.raises(RuntimeError, match=r"^RAGFlow retrieval failed$") as exc_info:
        adapter.retrieve(dataset_ids=["dataset-1"], question="policy")

    assert "secret-key" not in str(exc_info.value)


@pytest.mark.parametrize("max_chunks", [0, 21])
def test_retrieve_limits_result_window(
    rendered_modules: dict[str, ModuleType], tmp_path: Path, max_chunks: int
) -> None:
    """Agent-selected result limits stay within a small, predictable window."""
    adapter = rendered_modules["ragflow"].RAGFlowAdapter(client=object(), upload_root=tmp_path)

    with pytest.raises(ValueError, match="max_chunks must be between 1 and 20"):
        adapter.retrieve(
            dataset_ids=["dataset-1"],
            question="policy",
            max_chunks=max_chunks,
        )
