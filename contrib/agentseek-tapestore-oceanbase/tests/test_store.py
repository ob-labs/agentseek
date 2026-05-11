from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from agentseek_tapestore_oceanbase.store import OceanBaseTapeStore
from agentseek_tapestore_oceanbase.vector_support import OceanBaseVectorEnhancer, normalize_vector_metric
from republic import RepublicError, TapeEntry, TapeQuery


def _store(tmp_path: Path, **kwargs) -> OceanBaseTapeStore:
    return OceanBaseTapeStore(f"sqlite+pysqlite:///{tmp_path / 'tapes.db'}", **kwargs)


def _embedding_response(vectors: list[list[float]]) -> SimpleNamespace:
    return SimpleNamespace(
        data=[SimpleNamespace(embedding=vector) for vector in vectors],
    )


def test_sqlite_path_still_uses_base_sqlalchemy_behavior(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append("a__1", TapeEntry.message({"content": "hello"}))
    store.append("a__1", TapeEntry.anchor("phase-1"))
    store.append("a__1", TapeEntry.message({"content": "world"}))

    assert store.list_tapes() == ["a__1"]
    assert [entry.id for entry in TapeQuery("a__1", store).all()] == [1, 2, 3]
    assert [entry.payload.get("content") for entry in TapeQuery("a__1", store).after_anchor("phase-1").all()] == [
        "world"
    ]


def test_sqlite_query_falls_back_to_base_text_search_even_with_embedding_model(tmp_path: Path) -> None:
    store = _store(tmp_path, embedding_model="openai:text-embedding-3-small")
    store.append("room__1", TapeEntry.message({"content": "old timeout"}))
    store.append("room__1", TapeEntry.message({"content": "new timeout"}))

    entries = list(TapeQuery("room__1", store).query("timeout").limit(1).all())

    assert [entry.payload["content"] for entry in entries] == ["new timeout"]
    assert store._vector_enhancer is None


def test_append_is_safe_across_store_instances(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'shared.db'}"
    tape = "shared__1"
    writers = [OceanBaseTapeStore(database_url) for _ in range(4)]

    def _append_range(writer_index: int) -> None:
        store = writers[writer_index]
        for offset in range(25):
            store.append(
                tape,
                TapeEntry.message({"content": f"writer-{writer_index}", "offset": offset}),
            )

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(_append_range, range(4)))

    entries = list(TapeQuery(tape, OceanBaseTapeStore(database_url)).all())

    assert len(entries) == 100
    assert [entry.id for entry in entries] == list(range(1, 101))


def test_query_missing_anchor_matches_builtin_error_shape(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tape = "session__3"
    store.append(tape, TapeEntry.message({"content": "hello"}))

    with pytest.raises(RepublicError, match=r"Anchor 'missing' was not found\."):
        list(TapeQuery(tape, store).after_anchor("missing").all())


def test_store_constructor_validates_url() -> None:
    with pytest.raises(ValueError, match="Invalid SQLAlchemy URL"):
        OceanBaseTapeStore("not a sqlalchemy url")


def test_entry_from_payload_round_trip() -> None:
    payload = {
        "id": 7,
        "kind": "message",
        "payload": {"content": "hello"},
        "meta": {"source": "test"},
        "date": "2026-03-08T00:00:00+00:00",
    }

    entry = OceanBaseTapeStore.entry_from_payload(payload)

    assert entry is not None
    assert json.loads(json.dumps(entry.payload)) == {"content": "hello"}


def test_normalize_vector_metric_rejects_invalid_value() -> None:
    with pytest.raises(ValueError, match="vector_metric"):
        normalize_vector_metric("dot")


def test_embedding_response_parser_validates_vectors() -> None:
    vectors = OceanBaseVectorEnhancer._embedding_response_to_vectors(_embedding_response([[1.0, 0.0], [0.2, 0.8]]))

    assert vectors == [[1.0, 0.0], [0.2, 0.8]]
