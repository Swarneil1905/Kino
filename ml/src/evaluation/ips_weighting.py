"""IPS-weighted NDCG for popularity-bias correction."""

from __future__ import annotations

import numpy as np

from ml.src.evaluation.metrics import ndcg_at_k


def item_propensities(rating_counts: dict[int, int], min_prop: float = 0.01) -> dict[int, float]:
    if not rating_counts:
        return {}
    max_count = max(rating_counts.values())
    return {
        mid: max(count / max_count, min_prop)
        for mid, count in rating_counts.items()
    }


def ips_ndcg_at_k(
    recommended: list[list[int]],
    relevant: list[set[int]],
    propensities: dict[int, float],
    k: int = 10,
) -> float:
    scores = []
    for rec, rel in zip(recommended, relevant):
        if not rel:
            continue
        dcg = 0.0
        for i, item in enumerate(rec[:k]):
            if item in rel:
                weight = 1.0 / propensities.get(item, 0.01)
                dcg += weight / np.log2(i + 2)
        ideal_hits = sorted(
            [(1.0 / propensities.get(item, 0.01)) for item in rel],
            reverse=True,
        )[:k]
        ideal = sum(g / np.log2(i + 2) for i, g in enumerate(ideal_hits))
        scores.append(dcg / ideal if ideal > 0 else 0.0)
    return float(np.mean(scores)) if scores else 0.0
