from __future__ import annotations

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")

import pytest

from {{ cookiecutter.project_slug }} import agent
from {{ cookiecutter.project_slug }}.agent import _serialize_trace
from {{ cookiecutter.project_slug }}.models import SearchHit, SearchTrace, SearchWeights
from {{ cookiecutter.project_slug }}.settings import Settings


def test_serialize_trace_includes_developer_diagnostics() -> None:
    trace = SearchTrace(
        query="golden retriever",
        mode="exact",
        weights=SearchWeights(vector=0.1, sparse=0.2, fulltext=0.6, metadata=0.1),
        route_counts={"vector": 3, "sparse": 2, "fulltext": 1, "metadata": 1},
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
    assert artifact["weights"]["fulltext"] == 0.6
    assert artifact["route_counts"]["vector"] == 3


def test_prepare_search_request_clamps_top_k_and_rejects_empty_query(tmp_path) -> None:
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
        hybrid_max_top_k=3,
        media_data_dir=tmp_path / "media",
        media_max_upload_bytes=1024,
    )

    assert hasattr(agent, "_prepare_search_request")
    assert agent._prepare_search_request("  red label  ", 999, settings) == ("red label", 3)
    with pytest.raises(ValueError, match="query is required"):
        agent._prepare_search_request(" ", 1, settings)
