from __future__ import annotations

from {{ cookiecutter.project_slug }}.middleware import HYBRID_MODE_GUIDANCE


def test_hybrid_mode_guidance_names_all_modes() -> None:
    for mode in ("semantic", "keyword", "exact", "balanced"):
        assert mode in HYBRID_MODE_GUIDANCE
    assert "hybrid_search_knowledge_base" in HYBRID_MODE_GUIDANCE
