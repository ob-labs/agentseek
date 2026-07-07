from __future__ import annotations

from .sample_pack import sample_pack_cases
from .store import HybridImageStore


def _print_trace(case_id: str, mode: str, trace) -> None:
    print(f"\n[{case_id}] {mode} mode")
    print(f"  weights: V={trace.weights.vector:.0%} S={trace.weights.sparse:.0%} F={trace.weights.fulltext:.0%}")
    print(f"  route counts: {trace.route_counts}")
    for hit in trace.hits[:5]:
        score = "" if hit.fused_score is None else f" score={hit.fused_score:.3f}"
        print(f"  {hit.rank}. {hit.file_name}{score} :: {hit.caption[:100]}")


def main() -> None:
    store = HybridImageStore()
    for case in sample_pack_cases():
        query = case["query"]
        print(f"\n=== {case['id']}: {query} ===")
        print(f"Expected effect: {case['expected_effect']}")
        traces = store.compare_modes(query, top_k=5)
        for mode in ("semantic", "keyword", "exact", "balanced"):
            _print_trace(case["id"], mode, traces[mode])


if __name__ == "__main__":
    main()
