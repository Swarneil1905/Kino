"""Recall@K and NDCG@K evaluation metrics."""

from __future__ import annotations

import numpy as np


def recall_at_k(recommended: list[list[int]], relevant: list[set[int]], k: int = 10) -> float:
    scores = []
    for rec, rel in zip(recommended, relevant):
        if not rel:
            continue
        hits = len(set(rec[:k]) & rel)
        scores.append(hits / len(rel))
    return float(np.mean(scores)) if scores else 0.0


def ndcg_at_k(recommended: list[list[int]], relevant: list[set[int]], k: int = 10) -> float:
    scores = []
    for rec, rel in zip(recommended, relevant):
        if not rel:
            continue
        dcg = sum(1.0 / np.log2(i + 2) for i, item in enumerate(rec[:k]) if item in rel)
        ideal = sum(1.0 / np.log2(i + 2) for i in range(min(len(rel), k)))
        scores.append(dcg / ideal if ideal > 0 else 0.0)
    return float(np.mean(scores)) if scores else 0.0
