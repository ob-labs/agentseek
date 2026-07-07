from __future__ import annotations

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from {{ cookiecutter.project_slug }}.agent import _serialize_trace
from {{ cookiecutter.project_slug }}.models import SearchHit, SearchTrace, SearchWeights


def test_serialize_trace_includes_developer_diagnostics() -> None:
    trace = SearchTrace(
        query="golden retriever",
        mode="exact",
        weights=SearchWeights(vector=0.1, sparse=0.2, fulltext=0.7),
        route_counts={"vector": 3, "sparse": 2, "fulltext": 1},
        hits=[
            SearchHit(
                image_id="dog-1",
                file_name="dog.jpg",
                image_url="/custom/media/images/dog-1",
                caption="golden retriever in grass",
                rank=1,
                fused_score=0.9,
            )
        ],
        explanation="exact mode uses fulltext heavily.",
    )

    content, artifact = _serialize_trace(trace)

    assert "golden retriever" in content
    assert artifact["mode"] == "exact"
    assert artifact["weights"]["fulltext"] == 0.7
    assert artifact["route_counts"]["vector"] == 3
