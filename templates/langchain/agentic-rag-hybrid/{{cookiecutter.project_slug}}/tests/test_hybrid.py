from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from langchain_core.documents import Document

from {{ cookiecutter.project_slug }}.hybrid import normalize_search_mode, weighted_fuse, weights_for_mode
from {{ cookiecutter.project_slug }}.models import SearchHit
from {{ cookiecutter.project_slug }}.sample_pack import sample_pack_dir, sample_pack_manifest
from {{ cookiecutter.project_slug }}.settings import Settings
from {{ cookiecutter.project_slug }}.store import (
    HybridImageEmbeddings,
    HybridImageStore,
    _format_trace,
    _image_id,
    _sparse_vector,
)


def hit(image_id: str, rank: int, matched_terms: list[str] | None = None) -> SearchHit:
    return SearchHit(
        image_id=image_id,
        file_name=f"{image_id}.png",
        image_url=f"/custom/media/images/{image_id}",
        caption=f"caption {image_id}",
        rank=rank,
        matched_terms=matched_terms or [],
    )


def test_normalize_search_mode_defaults_unknown_values() -> None:
    assert normalize_search_mode("semantic") == "semantic"
    assert normalize_search_mode("KEYWORD") == "keyword"
    assert normalize_search_mode("not-real") == "balanced"
    assert normalize_search_mode(None) == "balanced"


def test_weights_for_mode_exposes_distinct_routes() -> None:
    assert weights_for_mode("semantic").vector > weights_for_mode("semantic").fulltext
    assert weights_for_mode("keyword").sparse > weights_for_mode("keyword").vector
    assert weights_for_mode("exact").fulltext > weights_for_mode("exact").vector


def test_weighted_fuse_promotes_route_with_selected_weight() -> None:
    fused = weighted_fuse(
        vector_hits=[hit("a", 1)],
        sparse_hits=[hit("b", 1)],
        fulltext_hits=[hit("b", 1)],
        metadata_hits=[],
        weights=weights_for_mode("keyword"),
        top_k=2,
    )

    assert [item.image_id for item in fused] == ["b", "a"]
    assert fused[0].fused_score and fused[0].fused_score > fused[1].fused_score


def test_weighted_fuse_can_promote_metadata_route() -> None:
    fused = weighted_fuse(
        vector_hits=[hit("a", 1)],
        sparse_hits=[],
        fulltext_hits=[],
        metadata_hits=[hit("metadata-match", 1)],
        weights=weights_for_mode("keyword"),
        top_k=2,
    )

    assert fused[0].image_id == "metadata-match"
    assert fused[0].metadata_score


def test_weighted_fuse_merges_matched_terms_from_all_routes() -> None:
    fused = weighted_fuse(
        vector_hits=[hit("same", 1)],
        sparse_hits=[hit("same", 1, matched_terms=["fragile", "a17"])],
        fulltext_hits=[],
        metadata_hits=[hit("same", 1, matched_terms=["shipping"])],
        weights=weights_for_mode("balanced"),
        top_k=1,
    )

    assert fused[0].matched_terms == ["fragile", "a17", "shipping"]


def test_hit_from_document_prefers_persisted_image_id(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )
    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings

    hit = store._hit_from_document(
        Document(
            id="internal-row-id",
            page_content="caption",
            metadata={"image_id": "stable-image-id", "file_name": "image.png"},
        ),
        rank=1,
        distance=None,
    )

    assert hit.image_id == "stable-image-id"
    assert hit.image_url == "/custom/media/images/stable-image-id"


def test_format_trace_includes_mode_weights_and_route_counts() -> None:
    trace = _format_trace(
        query="red trail shoe",
        mode="keyword",
        vector_hits=[hit("a", 1)],
        sparse_hits=[hit("b", 1)],
        fulltext_hits=[hit("b", 1)],
        metadata_hits=[hit("c", 1)],
        top_k=2,
    )

    assert trace.mode == "keyword"
    assert trace.route_counts == {"vector": 1, "sparse": 1, "fulltext": 1, "metadata": 1}
    assert "keyword" in trace.explanation
    assert trace.hits[0].image_id == "b"


def test_search_routes_use_distinct_sparse_fulltext_and_metadata_candidates(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    class FakeEmbeddingEngine:
        seen_text: str | None = None

        def embed_text(self, text: str) -> list[float]:
            self.seen_text = text
            return [0.1, 0.2, 0.3, 0.4]

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.vector_calls: list[dict] = []
            self.fulltext_calls: list[dict] = []
            self.sparse_calls: list[dict] = []
            self.ids_calls: list[list[str]] = []

        def similarity_search_with_score_by_vector(self, embedding, k: int):
            self.vector_calls.append({"embedding": embedding, "k": k})
            return [
                (
                    Document(
                        id="vector",
                        page_content="semantic result",
                        metadata={"file_name": "semantic.png", "file_path": str(tmp_path / "semantic.png")},
                    ),
                    0.1,
                )
            ]

        def advanced_hybrid_search(self, **kwargs):
            self.fulltext_calls.append(kwargs)
            return [
                Document(
                    id="fulltext",
                    page_content="red product label",
                    metadata={"file_name": "red-label.png", "file_path": str(tmp_path / "red-label.png")},
                )
            ]

        def similarity_search_with_sparse_vector(self, sparse_query, k: int):
            self.sparse_calls.append({"sparse_query": sparse_query, "k": k})
            return [
                Document(
                    id="sparse-red",
                    page_content="red product label token",
                    metadata={
                        "file_name": "token.png",
                        "file_path": str(tmp_path / "token.png"),
                        "caption": "red product label token",
                    },
                )
            ]

        def get_by_ids(self, ids):
            self.ids_calls.append(list(ids))
            return [
                Document(
                    id="metadata",
                    page_content="metadata candidate",
                    metadata={
                        "file_name": "red-product.png",
                        "file_path": str(tmp_path / "red-product.png"),
                        "tags": "catalog",
                    },
                )
            ]

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    engine = FakeEmbeddingEngine()
    store.embedding_engine = engine
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store
    store._load_index_ids = lambda: ["sparse-red", "metadata"]

    trace = store.search_text("red product label", mode="keyword", top_k=3)

    assert vector_store.fulltext_calls[0]["fulltext_query"] == "red product label"
    assert vector_store.fulltext_calls[0]["modality_weights"] == {"vector": 0.0, "sparse": 0.0, "fulltext": 1.0}
    assert vector_store.sparse_calls[0]["sparse_query"] == _sparse_vector("red product label")
    assert vector_store.ids_calls == [["sparse-red", "metadata"]]
    assert trace.route_counts["sparse"] == 1
    assert trace.route_counts["metadata"] == 1
    assert trace.hits[0].matched_terms
    assert engine.seen_text == "red product label"
    assert vector_store.vector_calls[0]["embedding"] == [0.1, 0.2, 0.3, 0.4]


def test_compare_modes_reuses_one_retrieval_for_all_mode_traces(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    class RecordingEmbeddingEngine:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def embed_text(self, text: str) -> list[float]:
            self.calls.append(text)
            return [0.1, 0.2, 0.3, 0.4]

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.vector_calls: list[dict] = []
            self.sparse_calls: list[dict] = []
            self.fulltext_calls: list[dict] = []
            self.ids_calls: list[list[str]] = []

        def similarity_search_with_score_by_vector(self, embedding, k: int):
            self.vector_calls.append({"embedding": embedding, "k": k})
            return [
                (
                    Document(
                        id="vector",
                        page_content="red product label",
                        metadata={"file_name": "vector.png"},
                    ),
                    0.1,
                )
            ]

        def similarity_search_with_sparse_vector(self, sparse_query, k: int):
            self.sparse_calls.append({"sparse_query": sparse_query, "k": k})
            return [
                Document(
                    id="sparse",
                    page_content="red product label",
                    metadata={"file_name": "sparse.png"},
                )
            ]

        def advanced_hybrid_search(self, **kwargs):
            self.fulltext_calls.append(kwargs)
            return [
                Document(
                    id="fulltext",
                    page_content="red product label",
                    metadata={"file_name": "fulltext.png"},
                )
            ]

        def get_by_ids(self, ids):
            self.ids_calls.append(list(ids))
            return [
                Document(
                    id="indexed",
                    page_content="red product label",
                    metadata={"file_name": "indexed.png", "tags": "red"},
                )
            ]

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    engine = RecordingEmbeddingEngine()
    store.embedding_engine = engine
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store
    store._load_index_ids = lambda: ["indexed"]

    traces = store.compare_modes("  red product label  ", top_k=3)

    assert set(traces) == {"balanced", "semantic", "keyword", "exact"}
    assert engine.calls == ["red product label"]
    assert len(vector_store.vector_calls) == 1
    assert len(vector_store.sparse_calls) == 1
    assert len(vector_store.fulltext_calls) == 1
    assert vector_store.ids_calls == [["indexed"]]
    expected_route_counts = {"vector": 1, "sparse": 2, "fulltext": 1, "metadata": 1}
    assert all(trace.route_counts == expected_route_counts for trace in traces.values())
    assert traces["semantic"].weights == weights_for_mode("semantic")
    assert traces["keyword"].weights == weights_for_mode("keyword")
    assert traces["exact"].weights == weights_for_mode("exact")


def test_sparse_hits_fall_back_to_indexed_docs_when_native_sparse_has_no_evidence(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.sparse_calls: list[dict] = []
            self.ids_calls: list[list[str]] = []

        def similarity_search_with_sparse_vector(self, sparse_query, k: int):
            self.sparse_calls.append({"sparse_query": sparse_query, "k": k})
            return [
                Document(
                    id="native-miss",
                    page_content="unrelated candidate",
                    metadata={"file_name": "native-miss.png", "caption": "unrelated candidate"},
                )
            ]

        def get_by_ids(self, ids):
            self.ids_calls.append(list(ids))
            return [
                Document(
                    id="fallback-hit",
                    page_content="A product package with a red tea label.",
                    metadata={"file_name": "red-tea-label.png", "caption": "A product package with a red tea label."},
                )
            ]

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store
    store._load_index_ids = lambda: ["fallback-hit"]

    hits = store._sparse_hits("red product tea label", recall=3)

    assert vector_store.sparse_calls[0]["sparse_query"] == _sparse_vector("red product tea label")
    assert vector_store.ids_calls == [["fallback-hit"]]
    assert hits[0].image_id == "fallback-hit"
    assert hits[0].matched_terms == ["red", "product", "tea", "label"]


def test_sparse_hits_rank_full_indexed_evidence_ahead_of_partial_native_hit(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.sparse_calls: list[dict] = []
            self.ids_calls: list[list[str]] = []

        def similarity_search_with_sparse_vector(self, sparse_query, k: int):
            self.sparse_calls.append({"sparse_query": sparse_query, "k": k})
            return [
                Document(
                    id="native-partial",
                    page_content="A red sticker on a jar.",
                    metadata={"file_name": "red-fragile-sticker.png", "caption": "A red sticker on a jar."},
                )
            ]

        def get_by_ids(self, ids):
            self.ids_calls.append(list(ids))
            return [
                Document(
                    id="indexed-full",
                    page_content="A product package with a red tea label.",
                    metadata={"file_name": "red-tea-label.png", "caption": "A product package with a red tea label."},
                )
            ]

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store
    store._load_index_ids = lambda: ["indexed-full"]

    hits = store._sparse_hits("red product tea label", recall=3)

    assert vector_store.sparse_calls[0]["sparse_query"] == _sparse_vector("red product tea label")
    assert hits[0].image_id == "indexed-full"
    assert hits[0].matched_terms == ["red", "product", "tea", "label"]


def test_sparse_and_metadata_routes_cap_auxiliary_index_candidates(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
        hybrid_auxiliary_candidate_limit=2,
    )

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.ids_calls: list[list[str]] = []

        def similarity_search_with_sparse_vector(self, sparse_query, k: int):
            return []

        def get_by_ids(self, ids):
            self.ids_calls.append(list(ids))
            return [
                Document(
                    id=image_id,
                    page_content=f"red product candidate {image_id}",
                    metadata={"file_name": f"{image_id}.png", "caption": f"red product candidate {image_id}"},
                )
                for image_id in ids
            ]

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store
    store._load_index_ids = lambda: [f"indexed-{index}" for index in range(10)]

    assert store._sparse_hits("red product", recall=4)
    metadata_hits = store._metadata_hits_from_index(["indexed", "red"], recall=4)

    assert vector_store.ids_calls == [["indexed-0", "indexed-1"], ["indexed-0", "indexed-1"]]
    assert len(metadata_hits) <= 2


def test_ingest_directory_embeds_each_real_sample_image_with_manifest_metadata(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )
    manifest = sample_pack_manifest()

    class FakeEmbeddingEngine:
        def __init__(self) -> None:
            self.image_paths: list[str] = []

        def embed_image(self, image_path) -> list[float]:
            self.image_paths.append(image_path.name)
            return [0.1, 0.2, 0.3, 0.4]

        def embed_text(self, text: str) -> list[float]:
            return [0.4, 0.3, 0.2, 0.1]

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.add_args = None
            self.embeddings: list[list[float]] = []

        def add_documents(self, documents, **kwargs):
            self.add_args = {"documents": documents, **kwargs}
            self.embeddings = store.embedding_adapter.embed_documents([document.page_content for document in documents])
            return kwargs["ids"]

    engine = FakeEmbeddingEngine()
    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    store.embedding_engine = engine
    store.embedding_adapter = HybridImageEmbeddings(engine)
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store

    records = store.ingest_directory(sample_pack_dir() / "images")

    manifest_by_file = {item["file_name"]: item for item in manifest["images"]}
    assert set(engine.image_paths) == {record.file_path.name for record in records}
    assert all(record.file_path.parent == settings.media_data_dir / "images" for record in records)
    assert vector_store.add_args is not None
    assert [document.page_content for document in vector_store.add_args["documents"]] == [
        manifest_by_file[record.file_name]["caption"]
        for record in records
    ]
    assert {
        document.metadata["manifest_id"]
        for document in vector_store.add_args["documents"]
    } == {item["id"] for item in manifest["images"]}
    assert {
        document.metadata["image_id"]
        for document in vector_store.add_args["documents"]
    } == set(vector_store.add_args["ids"])
    assert {
        document.id
        for document in vector_store.add_args["documents"]
    } == set(vector_store.add_args["ids"])
    assert all(extra["sparse_embedding"] for extra in vector_store.add_args["extras"])
    assert all("fulltext_content" in extra for extra in vector_store.add_args["extras"])
    assert set(store._load_index_ids()) == set(vector_store.add_args["ids"])


def _controlled_ingestion_store(tmp_path: Path, confirmed_indexes: list[int]):
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    class FakeEmbeddingEngine:
        def embed_image(self, image_path: Path) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4]

        def embed_text(self, text: str) -> list[float]:
            return [0.4, 0.3, 0.2, 0.1]

    class ControlledVectorStore:
        def __init__(self) -> None:
            self.requested_ids: list[str] = []

        def add_documents(self, documents, **kwargs):
            self.requested_ids = [str(image_id) for image_id in kwargs["ids"]]
            return [self.requested_ids[index] for index in confirmed_indexes]

    engine = FakeEmbeddingEngine()
    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    store.embedding_engine = engine
    store.embedding_adapter = HybridImageEmbeddings(engine)
    vector_store = ControlledVectorStore()
    store.vector_store = vector_store
    return store, vector_store


def test_ingest_directory_rejects_zero_confirmed_vector_store_inserts(tmp_path) -> None:
    store, _ = _controlled_ingestion_store(tmp_path, confirmed_indexes=[])

    with pytest.raises(RuntimeError, match="confirmed 0 of"):
        store.ingest_directory(sample_pack_dir() / "images")

    assert store._load_index_ids() == []


def test_ingest_directory_records_confirmed_ids_but_rejects_partial_insert(tmp_path) -> None:
    store, vector_store = _controlled_ingestion_store(tmp_path, confirmed_indexes=[0])

    with pytest.raises(RuntimeError, match="confirmed 1 of"):
        store.ingest_directory(sample_pack_dir() / "images")

    assert store._load_index_ids() == vector_store.requested_ids[:1]


def test_image_id_sanitizes_url_path_segments_and_preserves_safe_short_stems(tmp_path: Path) -> None:
    def digest(path: Path) -> str:
        return hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:16]

    safe_path = tmp_path / "Display.PNG"
    fragment_path = tmp_path / "front#?% 1.png"
    unicode_path = tmp_path / "\u4e2d\u6587.png"
    overlong_path = tmp_path / f"{'a' * 100}.png"

    image_ids = [
        _image_id(safe_path),
        _image_id(fragment_path),
        _image_id(unicode_path),
        _image_id(overlong_path),
    ]

    assert image_ids == [
        f"Display-{digest(safe_path)}",
        f"front-1-{digest(fragment_path)}",
        f"image-{digest(unicode_path)}",
        f"{'a' * 64}-{digest(overlong_path)}",
    ]
    assert all(
        character.isascii() and (character.isalnum() or character in "._-")
        for image_id in image_ids
        for character in image_id
    )


def test_ingest_directory_copies_external_images_to_managed_media_storage(tmp_path) -> None:
    settings = Settings(
        seekdb_path=tmp_path / "seekdb",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="siliconflow",
        embedding_api_key="test",
        embedding_base_url="https://example.test/v1",
        embedding_model="test",
        embedding_dimension=4,
        vlm_api_key="",
        vlm_base_url="https://example.test",
        vlm_model="qwen-vl",
        hybrid_default_mode="balanced",
        hybrid_recall_multiplier=2,
        hybrid_max_top_k=5,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )
    source_dir = tmp_path / "custom-source"
    source_dir.mkdir()
    source_image = source_dir / "Display.PNG"
    source_image.write_bytes(b"external image content")
    (source_dir / "manifest.yml").write_text(
        "images:\n  - file_name: Display.PNG\n    caption: externally supplied image\n",
        encoding="utf-8",
    )

    class FakeEmbeddingEngine:
        def __init__(self) -> None:
            self.image_paths: list[Path] = []

        def embed_image(self, image_path: Path) -> list[float]:
            self.image_paths.append(image_path)
            return [0.1, 0.2, 0.3, 0.4]

        def embed_text(self, text: str) -> list[float]:
            return [0.4, 0.3, 0.2, 0.1]

    class RecordingVectorStore:
        def __init__(self) -> None:
            self.add_args = None

        def add_documents(self, documents, **kwargs):
            self.add_args = {"documents": documents, **kwargs}
            store.embedding_adapter.embed_documents([document.page_content for document in documents])
            return kwargs["ids"]

    engine = FakeEmbeddingEngine()
    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    store.embedding_engine = engine
    store.embedding_adapter = HybridImageEmbeddings(engine)
    vector_store = RecordingVectorStore()
    store.vector_store = vector_store

    records = store.ingest_directory(source_dir)

    expected_path = settings.media_data_dir / "images" / f"{_image_id(source_image)}.png"
    assert expected_path.read_bytes() == b"external image content"
    assert records[0].file_name == "Display.PNG"
    assert records[0].file_path == expected_path
    assert records[0].metadata["file_path"] == str(expected_path)
    assert engine.image_paths == [expected_path]
    assert vector_store.add_args["documents"][0].metadata["file_path"] == str(expected_path)
