from __future__ import annotations

from dataclasses import replace

from .models import SearchHit, SearchMode, SearchWeights

SEARCH_MODE_WEIGHTS: dict[SearchMode, SearchWeights] = {
    "semantic": SearchWeights(vector=0.7, sparse=0.2, fulltext=0.1),
    "keyword": SearchWeights(vector=0.2, sparse=0.6, fulltext=0.2),
    "exact": SearchWeights(vector=0.1, sparse=0.2, fulltext=0.7),
    "balanced": SearchWeights(vector=0.4, sparse=0.3, fulltext=0.3),
}


def normalize_search_mode(value: str | None) -> SearchMode:
    if value is None:
        return "balanced"
    normalized = value.strip().lower()
    if normalized in SEARCH_MODE_WEIGHTS:
        return normalized  # type: ignore[return-value]
    return "balanced"


def weights_for_mode(mode: SearchMode) -> SearchWeights:
    return SEARCH_MODE_WEIGHTS[mode]


def _route_score(rank: int) -> float:
    return 1.0 / rank


def weighted_fuse(
    vector_hits: list[SearchHit],
    sparse_hits: list[SearchHit],
    fulltext_hits: list[SearchHit],
    weights: SearchWeights,
    top_k: int,
) -> list[SearchHit]:
    by_id: dict[str, SearchHit] = {}
    scores: dict[str, dict[str, float]] = {}

    for route, route_hits, weight in (
        ("vector", vector_hits, weights.vector),
        ("sparse", sparse_hits, weights.sparse),
        ("fulltext", fulltext_hits, weights.fulltext),
    ):
        for rank, hit in enumerate(route_hits, start=1):
            by_id.setdefault(hit.image_id, hit)
            scores.setdefault(hit.image_id, {})[route] = _route_score(rank) * weight

    ranked: list[SearchHit] = []
    for image_id, route_scores in scores.items():
        total = sum(route_scores.values())
        hit = by_id[image_id]
        ranked.append(
            replace(
                hit,
                fused_score=total,
                vector_score=route_scores.get("vector"),
                sparse_score=route_scores.get("sparse"),
                fulltext_score=route_scores.get("fulltext"),
            )
        )

    ranked.sort(key=lambda hit: (hit.fused_score or 0.0, hit.file_name), reverse=True)
    return [replace(hit, rank=index + 1) for index, hit in enumerate(ranked[:top_k])]
