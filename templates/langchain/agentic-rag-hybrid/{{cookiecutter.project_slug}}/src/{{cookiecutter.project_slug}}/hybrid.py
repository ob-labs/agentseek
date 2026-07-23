from __future__ import annotations

from dataclasses import replace

from .models import SearchHit, SearchMode, SearchWeights

SEARCH_MODE_WEIGHTS: dict[SearchMode, SearchWeights] = {
    "semantic": SearchWeights(vector=0.65, sparse=0.15, fulltext=0.10, metadata=0.10),
    "keyword": SearchWeights(vector=0.15, sparse=0.45, fulltext=0.15, metadata=0.25),
    "exact": SearchWeights(vector=0.10, sparse=0.15, fulltext=0.55, metadata=0.20),
    "balanced": SearchWeights(vector=0.35, sparse=0.25, fulltext=0.25, metadata=0.15),
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


def normalize_query(value: str) -> str:
    query = value.strip()
    if not query:
        raise ValueError("query is required")
    return query


def clamp_top_k(value: int, max_top_k: int) -> int:
    return min(max(1, value), max_top_k)


def _route_score(rank: int) -> float:
    return 1.0 / rank


def weighted_fuse(
    vector_hits: list[SearchHit],
    sparse_hits: list[SearchHit],
    fulltext_hits: list[SearchHit],
    metadata_hits: list[SearchHit],
    weights: SearchWeights,
    top_k: int,
) -> list[SearchHit]:
    by_id: dict[str, SearchHit] = {}
    scores: dict[str, dict[str, float]] = {}
    matched_terms: dict[str, list[str]] = {}

    for route, route_hits, weight in (
        ("vector", vector_hits, weights.vector),
        ("sparse", sparse_hits, weights.sparse),
        ("fulltext", fulltext_hits, weights.fulltext),
        ("metadata", metadata_hits, weights.metadata),
    ):
        for rank, hit in enumerate(route_hits, start=1):
            by_id.setdefault(hit.image_id, hit)
            scores.setdefault(hit.image_id, {})[route] = _route_score(rank) * weight
            terms = matched_terms.setdefault(hit.image_id, [])
            for term in hit.matched_terms:
                if term not in terms:
                    terms.append(term)

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
                metadata_score=route_scores.get("metadata"),
                matched_terms=matched_terms.get(image_id, hit.matched_terms),
            )
        )

    ranked.sort(key=lambda hit: (-(hit.fused_score or 0.0), hit.file_name))
    return [replace(hit, rank=index + 1) for index, hit in enumerate(ranked[:top_k])]
