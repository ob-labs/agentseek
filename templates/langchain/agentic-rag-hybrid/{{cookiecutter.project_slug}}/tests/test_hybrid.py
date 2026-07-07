from __future__ import annotations

from {{ cookiecutter.project_slug }}.hybrid import normalize_search_mode, weighted_fuse, weights_for_mode
from {{ cookiecutter.project_slug }}.models import SearchHit
from {{ cookiecutter.project_slug }}.store import _format_trace


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
        weights=weights_for_mode("keyword"),
        top_k=2,
    )

    assert [item.image_id for item in fused] == ["b", "a"]
    assert fused[0].fused_score and fused[0].fused_score > fused[1].fused_score


def test_format_trace_includes_mode_weights_and_route_counts() -> None:
    trace = _format_trace(
        query="red trail shoe",
        mode="keyword",
        vector_hits=[hit("a", 1)],
        sparse_hits=[hit("b", 1)],
        fulltext_hits=[hit("b", 1)],
        top_k=2,
    )

    assert trace.mode == "keyword"
    assert trace.route_counts == {"vector": 1, "sparse": 1, "fulltext": 1}
    assert "keyword" in trace.explanation
    assert trace.hits[0].image_id == "b"
