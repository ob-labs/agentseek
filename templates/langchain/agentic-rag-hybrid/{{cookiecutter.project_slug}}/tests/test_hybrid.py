from __future__ import annotations

from {{ cookiecutter.project_slug }}.hybrid import normalize_search_mode, weighted_fuse, weights_for_mode
from {{ cookiecutter.project_slug }}.models import SearchHit
from {{ cookiecutter.project_slug }}.settings import Settings
from {{ cookiecutter.project_slug }}.store import HybridImageStore, _format_trace


def hit(image_id: str, rank: int) -> SearchHit:
    return SearchHit(
        image_id=image_id,
        file_name=f"{image_id}.png",
        image_url=f"/custom/media/images/{image_id}",
        caption=f"caption {image_id}",
        rank=rank,
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
        seekdb_host="127.0.0.1",
        seekdb_port="2881",
        seekdb_user="root",
        seekdb_password="",
        seekdb_db_name="test",
        image_table_name="images",
        embedding_type="dashscope",
        embedding_api_key="test",
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
        def embed_text(self, text: str) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4]

    class RecordingCollection:
        def __init__(self) -> None:
            self.get_calls: list[dict] = []

        def query(self, **kwargs):
            return {
                "ids": [["vector"]],
                "metadatas": [[{"file_name": "semantic.png", "file_path": str(tmp_path / "semantic.png")}]],
                "documents": [["semantic result"]],
                "distances": [[0.1]],
            }

        def get(self, **kwargs):
            self.get_calls.append(kwargs)
            where_document = kwargs.get("where_document") or {}
            term = where_document.get("$contains")
            if term == "red product label":
                return {
                    "ids": ["fulltext"],
                    "metadatas": [{"file_name": "red-label.png", "file_path": str(tmp_path / "red-label.png")}],
                    "documents": ["red product label"],
                }
            if term:
                return {
                    "ids": [f"sparse-{term}"],
                    "metadatas": [{"file_name": f"{term}.png", "file_path": str(tmp_path / f"{term}.png")}],
                    "documents": [f"{term} token"],
                }
            return {
                "ids": ["metadata"],
                "metadatas": [{"file_name": "red-product.png", "file_path": str(tmp_path / "red-product.png"), "tags": "label"}],
                "documents": ["metadata candidate"],
            }

    store = HybridImageStore.__new__(HybridImageStore)
    store.settings = settings
    store.embedding_engine = FakeEmbeddingEngine()
    store.collection = RecordingCollection()

    trace = store.search_text("red product label", mode="keyword", top_k=3)

    contains_values = [
        call.get("where_document", {}).get("$contains")
        for call in store.collection.get_calls
        if call.get("where_document")
    ]
    assert "red product label" in contains_values
    assert {"red", "product", "label"}.issubset(set(contains_values))
    assert any("where_document" not in call for call in store.collection.get_calls)
    assert trace.route_counts["metadata"] == 1
