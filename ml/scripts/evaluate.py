#!/usr/bin/env python3
"""
Offline evaluation for the Kino two-tower recommendation model.

Metrics:
  hit_rate@K           % of users where ≥1 held-out liked movie is in top-K
  ndcg@K               Normalised Discounted Cumulative Gain at cutoff K
  precision@K          Fraction of top-K that are held-out liked movies
  intra_list_distance  Mean pairwise cosine distance in the rec list
                       (higher = more diverse; range 0–2 for L2-normalised vecs)

Usage (from kino root):
  python -m ml.scripts.evaluate              # baseline (no MMR)
  python -m ml.scripts.evaluate --mmr        # with MMR reranking (λ=0.7)
  python -m ml.scripts.evaluate --compare    # run both, print table, save JSON
  python -m ml.scripts.evaluate --compare --n 200   # faster run with 200 users
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.src.data.features import GENRES, GENRE_TO_IDX, parse_genres
from ml.src.models.user_tower import UserTower

ARTIFACTS   = ROOT / "ml" / "artifacts"
DATA_DIR    = ROOT / "ml" / "data"

K           = 10
MMR_LAMBDA  = 0.7
N_EVAL      = 500   # users to evaluate — 200 is fast, 500 is stable
MIN_RATINGS = 10    # skip users with fewer rated FAISS-movies than this


# ── Artifact loading ──────────────────────────────────────────────────────────

def load_artifacts():
    meta         = json.loads((ARTIFACTS / "model_meta.json").read_text())
    movie_id_map = {int(k): int(v)
                    for k, v in json.loads((ARTIFACTS / "movie_id_map.json").read_text()).items()}
    index        = faiss.read_index(str(ARTIFACTS / "faiss_index.bin"))

    user_tower = UserTower(num_users=meta["num_users"])
    user_tower.load_state_dict(
        torch.load(ARTIFACTS / "user_tower.pt", map_location="cpu", weights_only=False)
    )
    user_tower.eval()

    user_map = {int(k): int(v) for k, v in meta["user_map"].items()}
    return meta, movie_id_map, index, user_tower, user_map


# ── Data loading ──────────────────────────────────────────────────────────────

def load_filtered_ratings(faiss_movie_ids: set) -> pd.DataFrame:
    """Stream ratings.csv and keep only rows whose movieId is in the FAISS index."""
    DTYPES = {"userId": "int32", "movieId": "int32",
              "rating": "float32", "timestamp": "int32"}
    chunks = []
    for chunk in pd.read_csv(DATA_DIR / "ratings.csv", dtype=DTYPES, chunksize=500_000):
        mask = chunk["movieId"].isin(faiss_movie_ids)
        if mask.any():
            chunks.append(chunk[mask])
    return pd.concat(chunks, ignore_index=True)


# ── Feature helpers ───────────────────────────────────────────────────────────

def build_genre_affinity(user_ratings: pd.DataFrame,
                         movie_genres: dict) -> np.ndarray:
    vec    = np.zeros(len(GENRES), dtype=np.float32)
    counts = np.zeros(len(GENRES), dtype=np.float32)
    for _, r in user_ratings.iterrows():
        mid    = int(r["movieId"])
        genres = movie_genres.get(mid, [])
        weight = 1.0 if r["rating"] >= 4.0 else (-0.5 if r["rating"] < 2.5 else 0.0)
        if weight == 0:
            continue
        for g in genres:
            if g in GENRE_TO_IDX:
                idx          = GENRE_TO_IDX[g]
                vec[idx]    += weight
                counts[idx] += 1
    counts = np.where(counts > 0, counts, 1.0)
    return (vec / counts).astype(np.float32)


def get_user_embedding(uid_idx: int,
                       affinity: np.ndarray,
                       user_tower: UserTower) -> np.ndarray:
    with torch.no_grad():
        emb = user_tower(
            torch.tensor([uid_idx]),
            torch.zeros(1, 64),              # history (not used at inference)
            torch.tensor(affinity).unsqueeze(0),
        )
    return emb.numpy().astype(np.float32)


# ── Diversity metric ──────────────────────────────────────────────────────────

def intra_list_distance(embs: np.ndarray) -> float:
    """Mean pairwise cosine distance for L2-normalised embeddings.

    Cosine distance = 1 − dot(a, b) when ||a||=||b||=1.
    Range [0, 2]: 0 means all items identical, ~1 means random, 2 means perfectly opposed.
    """
    if len(embs) < 2:
        return 0.0
    sims = embs @ embs.T                          # (K, K) cosine similarity matrix
    n    = len(embs)
    triu = sims[np.triu_indices(n, k=1)]          # upper triangle, no diagonal
    return float(np.mean(1.0 - triu))


# ── MMR reranking ─────────────────────────────────────────────────────────────

def mmr_rerank(candidates:   list,
               item_embs:    dict,
               rel_scores:   dict,
               k:            int   = K,
               lam:          float = MMR_LAMBDA) -> list:
    """Maximal Marginal Relevance.

    Selects the next item that best balances:
      relevance    (λ)       — original ranking score
      dissimilarity (1−λ)   — max cosine similarity to already-selected items

    lam=1.0 → pure relevance (identical to baseline)
    lam=0.7 → default: 70% relevance, 30% diversity
    lam=0.0 → pure diversity
    """
    selected  = []
    remaining = [c for c in candidates if c in item_embs]

    while len(selected) < k and remaining:
        best, best_score = None, -np.inf
        for cand in remaining:
            rel = rel_scores.get(cand, 0.0)
            if selected:
                sim_max = max(
                    float(np.dot(item_embs[cand], item_embs[s]))
                    for s in selected
                )
            else:
                sim_max = 0.0
            score = lam * rel - (1 - lam) * sim_max
            if score > best_score:
                best, best_score = cand, score
        selected.append(best)
        remaining.remove(best)

    return selected


# ── Core eval loop ────────────────────────────────────────────────────────────

def run_eval(use_mmr: bool = False,
             lam:     float = MMR_LAMBDA,
             n_users: int   = N_EVAL) -> dict:

    label = f"MMR (λ={lam})" if use_mmr else "Baseline"
    print(f"\n{'='*60}")
    print(f"  Kino Offline Eval — {label}  |  K={K}  |  N≤{n_users} users")
    print(f"{'='*60}")

    # Load artifacts
    print("Loading model artifacts...")
    meta, movie_id_map, index, user_tower, user_map = load_artifacts()
    faiss_movie_ids = set(movie_id_map.values())

    # Pre-extract item embeddings from FAISS (needed for diversity + MMR)
    print(f"Extracting {index.ntotal} item embeddings from FAISS index...")
    raw_embs      = index.reconstruct_n(0, index.ntotal)   # (ntotal, embed_dim)
    all_item_embs = {movie_id_map[pos]: raw_embs[pos] for pos in range(index.ntotal)}

    # Load movie genre info
    movies_df    = pd.read_csv(DATA_DIR / "movies.csv")
    movies_df    = movies_df[movies_df["movieId"].isin(faiss_movie_ids)]
    movie_genres = {int(r.movieId): parse_genres(str(r.genres))
                    for r in movies_df.itertuples()}

    # Load filtered ratings (~30s for 25M row file)
    print("Loading ratings filtered to FAISS movies (this takes ~30s)...")
    ratings = load_filtered_ratings(faiss_movie_ids)

    # Select eval users: must be in user_map and have enough rated items
    eligible = [
        uid for uid in ratings["userId"].unique()
        if uid in user_map
        and len(ratings[ratings["userId"] == uid]) >= MIN_RATINGS
    ]
    rng        = np.random.default_rng(42)
    eval_users = rng.choice(eligible,
                            size=min(n_users, len(eligible)),
                            replace=False)
    print(f"Evaluating on {len(eval_users)} users...")

    # Per-user metrics
    hits, ndcgs, precisions, diversities = [], [], [], []

    for uid in tqdm(eval_users, desc=label):
        user_ratings = ratings[ratings["userId"] == uid].sort_values("timestamp")

        # Temporal split: 80% train, 20% test
        n_train  = max(1, int(len(user_ratings) * 0.8))
        train_df = user_ratings.iloc[:n_train]
        test_df  = user_ratings.iloc[n_train:]

        # Ground truth: test-set movies rated ≥ 4.0
        relevant = set(test_df[test_df["rating"] >= 4.0]["movieId"].astype(int))
        if not relevant:
            continue

        # User embedding
        affinity = build_genre_affinity(train_df, movie_genres)
        u_emb    = get_user_embedding(user_map[uid], affinity, user_tower)

        # FAISS ANN retrieval (top-200 candidates)
        _, faiss_idxs = index.search(u_emb, 200)
        candidates    = [movie_id_map[i] for i in faiss_idxs[0]
                         if 0 <= i < index.ntotal]

        # Remove already-rated items
        rated      = set(train_df["movieId"].astype(int))
        candidates = [c for c in candidates if c not in rated]
        if not candidates:
            continue

        # Ranking: MMR or greedy top-K
        if use_mmr:
            # Relevance proxy: inverse rank from FAISS (position 0 = most relevant)
            rel_scores = {c: 1.0 / (i + 1) for i, c in enumerate(candidates)}
            top_k      = mmr_rerank(candidates, all_item_embs, rel_scores, k=K, lam=lam)
        else:
            top_k = candidates[:K]

        if not top_k:
            continue

        # ── Compute metrics ────────────────────────────────────────────────────

        # NDCG@K
        dcg       = sum(1.0 / np.log2(i + 2)
                        for i, m in enumerate(top_k) if m in relevant)
        ideal_dcg = sum(1.0 / np.log2(i + 2)
                        for i in range(min(len(relevant), K)))
        ndcg      = dcg / ideal_dcg if ideal_dcg > 0 else 0.0

        # Hit rate@K
        hit  = int(any(m in relevant for m in top_k))

        # Precision@K
        prec = sum(1 for m in top_k if m in relevant) / K

        # Intra-list diversity
        rec_embs = np.array([all_item_embs[m] for m in top_k if m in all_item_embs])
        div      = intra_list_distance(rec_embs) if len(rec_embs) >= 2 else 0.0

        hits.append(hit)
        ndcgs.append(ndcg)
        precisions.append(prec)
        diversities.append(div)

    results = {
        "variant":             label,
        "mmr_lambda":          lam if use_mmr else None,
        "n_users_evaluated":   len(hits),
        "hit_rate_at_10":      round(float(np.mean(hits)), 4),
        "ndcg_at_10":          round(float(np.mean(ndcgs)), 4),
        "precision_at_10":     round(float(np.mean(precisions)), 4),
        "intra_list_distance": round(float(np.mean(diversities)), 4),
    }

    print(f"\n  hit_rate@10:          {results['hit_rate_at_10']:.4f}")
    print(f"  ndcg@10:              {results['ndcg_at_10']:.4f}")
    print(f"  precision@10:         {results['precision_at_10']:.4f}")
    print(f"  intra_list_distance:  {results['intra_list_distance']:.4f}"
          f"  ← diversity (higher = better)")

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Kino offline evaluation")
    parser.add_argument("--mmr",     action="store_true",
                        help="Enable MMR reranking")
    parser.add_argument("--compare", action="store_true",
                        help="Run baseline + MMR, print comparison table, save JSON")
    parser.add_argument("--lam",     type=float, default=MMR_LAMBDA,
                        help=f"MMR lambda (default {MMR_LAMBDA})")
    parser.add_argument("--n",       type=int,   default=N_EVAL,
                        help=f"Number of eval users (default {N_EVAL})")
    args = parser.parse_args()

    if args.compare:
        baseline = run_eval(use_mmr=False,               n_users=args.n)
        mmr_res  = run_eval(use_mmr=True, lam=args.lam, n_users=args.n)

        print("\n" + "=" * 62)
        print("  COMPARISON  (Baseline vs MMR)")
        print("=" * 62)
        print(f"  {'Metric':<26} {'Baseline':>10} {'MMR':>10} {'Δ':>10}")
        print(f"  {'-'*58}")
        for key in ("hit_rate_at_10", "ndcg_at_10",
                    "precision_at_10", "intra_list_distance"):
            b, m  = baseline[key], mmr_res[key]
            delta = f"{(m - b) / b * 100:+.1f}%" if b else "n/a"
            note  = "  ← diversity" if key == "intra_list_distance" else ""
            print(f"  {key:<26} {b:>10.4f} {m:>10.4f} {delta:>10}{note}")

        out_path = ARTIFACTS / "eval_results.json"
        out_path.write_text(json.dumps({"baseline": baseline, "mmr": mmr_res}, indent=2))
        print(f"\n  Results saved → {out_path}")

    elif args.mmr:
        run_eval(use_mmr=True, lam=args.lam, n_users=args.n)
    else:
        run_eval(use_mmr=False, n_users=args.n)


if __name__ == "__main__":
    main()
