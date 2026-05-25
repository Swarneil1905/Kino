#!/usr/bin/env python3
"""
Train two-tower recommendation model on MovieLens 25M.

Run from the kino root directory:
    python -m ml.scripts.train_movielens

Outputs artifacts to:
    ml/artifacts/           (intermediate)
    apps/api/app/artifacts/ (production - replaces demo weights)
"""

from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.src.data.features import (
    GENRES,
    GENRE_TO_IDX,
    build_item_features,
    parse_genres,
)
from ml.src.data.splitter import label_implicit, split_by_timestamp
from ml.src.evaluation.ips_weighting import ips_ndcg_at_k, item_propensities
from ml.src.evaluation.metrics import ndcg_at_k, recall_at_k
from ml.src.models.ranker import Ranker
from ml.src.models.two_tower import TwoTowerModel

DATA_DIR = ROOT / "ml" / "data"
ARTIFACTS = ROOT / "ml" / "artifacts"
API_ARTIFACTS = ROOT / "apps" / "api" / "app" / "artifacts"

# Training config
TOP_MOVIES = 3_000   # top N most-rated movies
MAX_USERS = 15_000   # cap total users (random sample if more)
MIN_RATINGS = 20     # minimum ratings per user
EMBED_DIM = 128
EPOCHS = 10
BATCH_SIZE = 1024   # larger batch for GPU
LR = 1e-3
WEIGHT_DECAY = 1e-4
EVAL_USERS = 200

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Data loading ──────────────────────────────────────────────────────────────

def load_and_filter(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Two-pass chunked loader — never allocates the full 25M rows at once."""
    CHUNK = 500_000
    CSV_DTYPES = {
        "userId": "int32",
        "movieId": "int32",
        "rating": "float32",
        "timestamp": "int32",
    }
    ratings_path = data_dir / "ratings.csv"

    # ── Pass 1: count movie frequencies ──────────────────────────────────────
    print("Loading MovieLens 25M — pass 1/2 (movie counts)...")
    t0 = time.time()
    movie_counts: dict[int, int] = {}
    for chunk in pd.read_csv(ratings_path, dtype=CSV_DTYPES, chunksize=CHUNK):
        for mid, cnt in chunk["movieId"].value_counts().items():
            movie_counts[mid] = movie_counts.get(mid, 0) + cnt
    top_movie_set = set(
        sorted(movie_counts, key=lambda x: movie_counts[x], reverse=True)[:TOP_MOVIES]
    )
    print(f"  Pass 1 done in {time.time()-t0:.1f}s — top {len(top_movie_set):,} movies identified")

    # ── Pass 2: stream-write filtered rows to temp CSV (zero large allocs) ────
    print("Loading MovieLens 25M — pass 2/2 (filter rows)...")
    t1 = time.time()
    tmp_path = data_dir / "_filtered_tmp.csv"
    first_write = True
    row_count = 0
    for chunk in pd.read_csv(ratings_path, dtype=CSV_DTYPES, chunksize=CHUNK):
        mask = chunk["movieId"].isin(top_movie_set)
        if mask.any():
            chunk[mask].to_csv(tmp_path, mode="a", header=first_write, index=False)
            row_count += mask.sum()
            first_write = False
    print(f"  Pass 2 done in {time.time()-t1:.1f}s — {row_count:,} rows written to temp CSV")

    # Read back the small filtered file
    ratings = pd.read_csv(tmp_path, dtype=CSV_DTYPES)
    tmp_path.unlink()  # clean up temp file

    # Apply MIN_RATINGS filter, then cap to MAX_USERS (random sample)
    user_counts = ratings.groupby("userId").size()
    eligible = user_counts[user_counts >= MIN_RATINGS].index
    if len(eligible) > MAX_USERS:
        rng = np.random.default_rng(42)
        eligible = rng.choice(eligible, size=MAX_USERS, replace=False)
    ratings = ratings[ratings["userId"].isin(eligible)].copy()

    movies = pd.read_csv(data_dir / "movies.csv")
    movies = movies[movies["movieId"].isin(ratings["movieId"].unique())]

    print(f"  Final: {len(ratings):,} ratings | "
          f"{ratings['userId'].nunique():,} users | "
          f"{ratings['movieId'].nunique():,} movies")
    return ratings, movies


# ── Vectorized affinity builder ───────────────────────────────────────────────

def fast_user_genre_affinity(ratings_df: pd.DataFrame, movie_genres: dict) -> dict:
    """Vectorized replacement for build_user_genre_affinity — no iterrows()."""
    n_genres = len(GENRES)
    df = ratings_df[ratings_df["movieId"].isin(movie_genres)].copy()
    df["weight"] = 0.0
    df.loc[df["rating"] >= 4.0, "weight"] = 1.0
    df.loc[df["rating"] < 2.5,  "weight"] = -0.5

    # Build (N, n_genres) genre vector array and weight each row by rating weight
    genre_vecs = np.array(
        [movie_genres.get(int(mid), np.zeros(n_genres)) for mid in df["movieId"]],
        dtype=np.float32,
    )
    weights = df["weight"].values[:, None].astype(np.float32)
    weighted = genre_vecs * weights  # (N, n_genres)

    # groupby userId, sum weighted genre vecs, then L1-normalise
    expanded = pd.DataFrame(weighted, index=df.index, columns=list(range(n_genres)))
    expanded["userId"] = df["userId"].values

    agg = expanded.groupby("userId").sum()
    norms = agg.abs().sum(axis=1).clip(lower=1.0)
    agg = agg.div(norms, axis=0)

    return {int(uid): row.values.astype(np.float32) for uid, row in agg.iterrows()}


# ── Dataset ───────────────────────────────────────────────────────────────────

class PairDataset(Dataset):
    """Pre-computes all arrays at init so __getitem__ is pure numpy — no pandas overhead."""

    def __init__(
        self,
        pairs: pd.DataFrame,
        user_map: dict,
        item_map: dict,
        item_feats_indexed: pd.DataFrame,
        affinities: dict,
    ) -> None:
        n_genres = len(GENRES)
        pairs = pairs.reset_index(drop=True)

        self.user_ids = np.array([user_map[int(u)] for u in pairs["userId"]], dtype=np.int64)
        self.item_ids = np.array([item_map[int(m)] for m in pairs["movieId"]], dtype=np.int64)

        # Pre-build genre + numeric matrices indexed by item embedding index
        n_items = max(item_map.values()) + 1
        genre_matrix   = np.zeros((n_items, n_genres), dtype=np.float32)
        numeric_matrix = np.zeros((n_items, 2),        dtype=np.float32)
        for mid, iid in item_map.items():
            if mid in item_feats_indexed.index:
                row = item_feats_indexed.loc[mid]
                genre_matrix[iid]   = np.array(row["genre_vec"], dtype=np.float32)
                numeric_matrix[iid] = np.array(
                    [row["release_decade"], row["log_pop_scaled"]], dtype=np.float32
                )

        self.genre_vecs = genre_matrix[self.item_ids]
        self.numerics   = numeric_matrix[self.item_ids]

        # Pre-build affinity matrix indexed by user embedding index
        n_users = max(user_map.values()) + 1
        aff_matrix = np.zeros((n_users, n_genres), dtype=np.float32)
        for uid, uidx in user_map.items():
            if uid in affinities:
                aff_matrix[uidx] = np.array(affinities[uid], dtype=np.float32)
        self.affinities = aff_matrix[self.user_ids]

    def __len__(self) -> int:
        return len(self.user_ids)

    def __getitem__(self, idx: int):
        return (
            int(self.user_ids[idx]),
            int(self.item_ids[idx]),
            torch.zeros(64),
            torch.from_numpy(self.affinities[idx]),
            torch.from_numpy(self.genre_vecs[idx]),
            torch.from_numpy(self.numerics[idx]),
        )


# ── Training ──────────────────────────────────────────────────────────────────

def train(model: TwoTowerModel, loader: DataLoader, epochs: int) -> None:
    model = model.to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    model.train()

    for epoch in range(epochs):
        total_loss = 0.0
        batches = 0
        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False)
        for batch in pbar:
            uid, iid, hist, aff, gvec, num = [t.to(DEVICE) for t in batch]
            optimizer.zero_grad()
            user_emb, item_emb = model(uid, iid, hist, aff, gvec, num)
            logits = model.compute_logits(user_emb, item_emb)
            labels = torch.arange(len(uid), device=DEVICE)
            loss = F.cross_entropy(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
            batches += 1
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        scheduler.step()
        avg = total_loss / max(batches, 1)
        print(f"  Epoch {epoch+1}/{epochs}  loss={avg:.4f}  lr={scheduler.get_last_lr()[0]:.2e}")


# ── FAISS index ───────────────────────────────────────────────────────────────

def build_faiss_index(
    model: TwoTowerModel,
    item_feats: pd.DataFrame,
    item_map: dict,
    numeric_cols: list[str],
) -> tuple[faiss.Index, dict]:
    model.eval()
    sorted_feats = item_feats.sort_values("movie_id")
    all_iids = [item_map[mid] for mid in sorted_feats["movie_id"]]
    genre_matrix = torch.tensor(
        np.stack(sorted_feats["genre_vec"].values), dtype=torch.float32
    )
    numeric_matrix = torch.tensor(
        sorted_feats[numeric_cols].values, dtype=torch.float32
    )
    iid_tensor = torch.tensor(all_iids)

    model = model.to(DEVICE)
    with torch.no_grad():
        item_embs = model.item_tower(
            iid_tensor.to(DEVICE), genre_matrix.to(DEVICE), numeric_matrix.to(DEVICE)
        ).cpu().numpy()

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(item_embs.astype(np.float32))

    # Map FAISS position → real movie_id
    faiss_to_movie = {i: int(mid) for i, mid in enumerate(sorted_feats["movie_id"])}
    return index, faiss_to_movie


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate(
    model: TwoTowerModel,
    index: faiss.Index,
    faiss_to_movie: dict,
    test_df: pd.DataFrame,
    user_map: dict,
    affinities: dict,
    popularity: dict,
) -> dict:
    model.eval()
    recommended, relevant = [], []
    test_users = [u for u in test_df["userId"].unique() if u in user_map][:EVAL_USERS]

    print(f"  Evaluating on {len(test_users)} users...")
    for uid in tqdm(test_users, leave=False):
        rel = set(
            test_df[(test_df.userId == uid) & (test_df.label == 1)]["movieId"].astype(int)
        )
        if not rel:
            continue
        uidx = user_map[uid]
        aff = torch.tensor(
            affinities.get(uid, np.zeros(len(GENRES))), dtype=torch.float32
        ).unsqueeze(0)
        hist = torch.zeros(1, 64)
        with torch.no_grad():
            uemb = model.user_tower(
                torch.tensor([uidx]).to(DEVICE), hist.to(DEVICE), aff.to(DEVICE)
            ).cpu().numpy()
        _, idxs = index.search(uemb.astype(np.float32), 10)
        rec = [faiss_to_movie[i] for i in idxs[0] if i in faiss_to_movie]
        recommended.append(rec)
        relevant.append(rel)

    props = item_propensities({int(k): int(v) for k, v in popularity.items()})
    return {
        "recall_at_10": recall_at_k(recommended, relevant, 10),
        "ndcg_at_10": ndcg_at_k(recommended, relevant, 10),
        "ips_ndcg_at_10": ips_ndcg_at_k(recommended, relevant, props, 10),
        "model_version": "movielens-25m-v1",
    }


# ── Export ────────────────────────────────────────────────────────────────────

def export_artifacts(
    model: TwoTowerModel,
    index: faiss.Index,
    faiss_to_movie: dict,
    user_map: dict,
    item_map: dict,
    scaler: StandardScaler,
    metrics: dict,
) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    API_ARTIFACTS.mkdir(parents=True, exist_ok=True)

    # movie_id_map: FAISS position → real movie_id (for inference)
    movie_id_map = {str(k): v for k, v in faiss_to_movie.items()}

    meta = {
        "num_users": len(user_map),
        "num_items": len(item_map),
        "user_map": {str(int(k)): int(v) for k, v in user_map.items()},
        "item_map": {str(int(k)): int(v) for k, v in item_map.items()},
        "embed_dim": EMBED_DIM,
        "genre_dim": len(GENRES),
    }

    ranker = Ranker()

    files = {
        "user_tower.pt": lambda p: torch.save(model.user_tower.state_dict(), p),
        "item_tower.pt": lambda p: torch.save(model.item_tower.state_dict(), p),
        "ranker.pt": lambda p: torch.save(ranker.state_dict(), p),
        "faiss_index.bin": lambda p: faiss.write_index(index, str(p)),
        "movie_id_map.json": lambda p: p.write_text(json.dumps(movie_id_map)),
        "model_meta.json": lambda p: p.write_text(json.dumps(meta, indent=2)),
        "genre_encoder.pkl": lambda p: p.write_bytes(pickle.dumps(GENRE_TO_IDX)),
        "feature_scaler.pkl": lambda p: p.write_bytes(pickle.dumps(scaler)),
        "eval_metrics.json": lambda p: p.write_text(json.dumps(metrics, indent=2)),
    }

    for name, write_fn in files.items():
        write_fn(ARTIFACTS / name)
        (API_ARTIFACTS / name).write_bytes((ARTIFACTS / name).read_bytes())
        print(f"  Saved {name}")

    print(f"\nArtifacts written to {API_ARTIFACTS}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    t_start = time.time()
    print("=" * 60)
    print("Kino — Two-Tower Training on MovieLens 25M")
    print("=" * 60)
    print(f"Device: {DEVICE}" + (f" ({torch.cuda.get_device_name(0)})" if DEVICE.type == "cuda" else ""))

    # 1. Load and filter
    ratings, movies = load_and_filter(DATA_DIR)

    # 2. Split
    print("\nSplitting by timestamp...")
    train_df, val_df, test_df = split_by_timestamp(ratings)
    for df in (train_df, val_df, test_df):
        df["label"] = df["rating"].apply(label_implicit)
        df.dropna(subset=["label"], inplace=True)
        df["label"] = df["label"].astype(int)

    print(f"  Train: {len(train_df):,}  Val: {len(val_df):,}  Test: {len(test_df):,}")

    # 3. Build mappings
    users = sorted(ratings["userId"].unique())
    items = sorted(movies["movieId"].unique())
    user_map = {u: i for i, u in enumerate(users)}
    item_map = {m: i for i, m in enumerate(items)}
    print(f"  {len(users):,} users  |  {len(items):,} items")

    # 4. Feature engineering
    print("\nBuilding features...")
    popularity = ratings.groupby("movieId").size().to_dict()
    item_feats = build_item_features(movies, popularity)

    movie_genres = {
        int(r.movieId): parse_genres(str(r.genres)) for r in movies.itertuples()
    }
    print("  Building user genre affinities (vectorized)...")
    affinities = fast_user_genre_affinity(train_df, movie_genres)

    scaler = StandardScaler()
    item_feats["log_pop_scaled"] = scaler.fit_transform(item_feats[["log_popularity"]])
    numeric_cols = ["release_decade", "log_pop_scaled"]
    item_feats_indexed = item_feats.set_index("movie_id")

    # 5. Build dataset
    train_pairs = train_df[train_df["label"] == 1].copy()
    print(f"\n  Training on {len(train_pairs):,} positive pairs")
    dataset = PairDataset(train_pairs, user_map, item_map, item_feats_indexed, affinities)
    loader = DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True, num_workers=0
    )

    # 6. Train
    print(f"\nTraining two-tower model ({EPOCHS} epochs)...")
    model = TwoTowerModel(num_users=len(users), num_items=len(items))
    train(model, loader, EPOCHS)

    # 7. Build FAISS index
    print("\nBuilding FAISS index...")
    index, faiss_to_movie = build_faiss_index(model, item_feats, item_map, numeric_cols)
    print(f"  Index contains {index.ntotal} item vectors")

    # 8. Evaluate
    print("\nEvaluating...")
    metrics = evaluate(model, index, faiss_to_movie, test_df, user_map, affinities, popularity)
    print(f"\n  Recall@10:     {metrics['recall_at_10']:.4f}")
    print(f"  NDCG@10:       {metrics['ndcg_at_10']:.4f}")
    print(f"  IPS-NDCG@10:   {metrics['ips_ndcg_at_10']:.4f}")

    # 9. Export
    print("\nExporting artifacts...")
    export_artifacts(model, index, faiss_to_movie, user_map, item_map, scaler, metrics)

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed/60:.1f} minutes.")
    print("Restart the API container to load the new weights:")
    print("  docker compose restart api")


if __name__ == "__main__":
    main()
