"""
Maximal Marginal Relevance (MMR) reranking for recommendation diversity.

MMR balances relevance and novelty when selecting the final recommendation list.
At each step it picks the candidate that maximises:

    score = λ · relevance(c) − (1−λ) · max_{s ∈ selected} sim(c, s)

Parameters
----------
lam : float
    Trade-off weight in [0, 1].
    lam = 1.0  →  pure relevance  (identical to greedy ranking)
    lam = 0.7  →  70% relevance + 30% diversity  ← production default
    lam = 0.0  →  pure diversity

Reference: Carbonell & Goldstein, 1998 — "The use of MMR, diversity-based
reranking for reordering documents and producing summaries"
"""
from __future__ import annotations

import numpy as np


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors.

    If vectors are already L2-normalised (as they are from both towers)
    this reduces to a simple dot product.
    """
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < 1e-8:
        return 0.0
    return float(np.dot(a, b) / denom)


def mmr_rerank(
    candidates:       list[int],
    item_embeddings:  dict[int, np.ndarray],
    relevance_scores: dict[int, float],
    k:                int   = 30,
    lam:              float = 0.7,
) -> list[int]:
    """Rerank *candidates* using Maximal Marginal Relevance.

    Parameters
    ----------
    candidates :
        Ordered list of candidate movie IDs (e.g. FAISS ANN results, already
        filtered for rated items). IDs not present in *item_embeddings* are skipped.
    item_embeddings :
        Mapping of movie_id → L2-normalised item embedding (numpy array).
        Typically populated from the FAISS index via ``index.reconstruct()``.
    relevance_scores :
        Mapping of movie_id → relevance score.  A simple inverse-rank proxy
        ``{c: 1/(i+1) for i, c in enumerate(candidates)}`` works well when
        no explicit score is available.
    k :
        Number of items to select.
    lam :
        Relevance–diversity trade-off (see module docstring).

    Returns
    -------
    list[int]
        Reranked list of up to *k* movie IDs.
    """
    # Only keep candidates that have an embedding
    pool = [c for c in candidates if c in item_embeddings]

    selected: list[int] = []

    while len(selected) < k and pool:
        best_id:    int   = pool[0]
        best_score: float = -np.inf

        for cand in pool:
            rel = relevance_scores.get(cand, 0.0)

            if selected:
                # Penalise by maximum similarity to anything already selected
                sim_max = max(
                    cosine_sim(item_embeddings[cand], item_embeddings[s])
                    for s in selected
                )
            else:
                sim_max = 0.0

            score = lam * rel - (1 - lam) * sim_max

            if score > best_score:
                best_score = score
                best_id    = cand

        selected.append(best_id)
        pool.remove(best_id)

    return selected


def intra_list_distance(movie_ids: list[int],
                        item_embeddings: dict[int, np.ndarray]) -> float:
    """Compute mean pairwise cosine distance for a recommendation list.

    Used as the diversity metric in offline evaluation and on the Metrics page.

    Returns a value in [0, 2] for L2-normalised embeddings.
    Higher is better: 0 means all items are identical, ~1 is typical for
    a well-trained model, 2 means maximally spread.
    """
    embs = [item_embeddings[mid] for mid in movie_ids if mid in item_embeddings]
    if len(embs) < 2:
        return 0.0
    arr  = np.stack(embs)          # (n, d)
    sims = arr @ arr.T             # (n, n) cosine similarity (vecs are normalised)
    n    = len(embs)
    triu = sims[np.triu_indices(n, k=1)]
    return float(np.mean(1.0 - triu))
