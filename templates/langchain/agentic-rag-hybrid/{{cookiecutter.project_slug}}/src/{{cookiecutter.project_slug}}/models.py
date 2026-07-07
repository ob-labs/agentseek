from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

SearchMode = Literal["balanced", "semantic", "keyword", "exact"]


@dataclass(frozen=True)
class SearchWeights:
    vector: float
    sparse: float
    fulltext: float
    metadata: float


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    file_name: str
    file_path: Path
    caption: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    image_id: str
    file_name: str
    image_url: str
    caption: str
    rank: int
    fused_score: float | None = None
    vector_score: float | None = None
    sparse_score: float | None = None
    fulltext_score: float | None = None
    metadata_score: float | None = None
    distance: float | None = None
    matched_terms: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchTrace:
    query: str
    mode: SearchMode
    weights: SearchWeights
    route_counts: dict[str, int]
    hits: list[SearchHit]
    explanation: str
