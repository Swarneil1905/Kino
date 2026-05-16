#!/usr/bin/env python3
"""Train a compact two-tower model on synthetic data and export API artifacts."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.src.data.features import GENRES, GENRE_TO_IDX, build_item_features, genre_multi_hot, log_popularity, release_decade
from ml.src.data.splitter import label_implicit, split_by_timestamp
from ml.src.evaluation.ips_weighting import ips_ndcg_at_k, item_propensities
from ml.src.evaluation.metrics import ndcg_at_k, recall_at_k
from ml.src.models.ranker import Ranker
from ml.src.models.two_tower import TwoTowerModel

ARTIFACTS = ROOT / "ml" / "artifacts"
API_ARTIFACTS = ROOT / "apps" / "api" / "app" / "artifacts"
NUM_MOVIES = 2000
NUM_USERS = 5000
EMBED_DIM = 128
EPOCHS = 5
BATCH_SIZE = 512


def generate_synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(42)
    movies = []
    genres_pool = list(GENRE_TO_IDX.keys())
    for mid in range(1, NUM_MOVIES + 1):
        n_genres = rng.integers(1, 4)
        genres = "|".join(rng.choice(genres_pool, size=n_genres, replace=False))
        year = int(rng.integers(1980, 2024))
        movies.append({"movieId": mid, "title": f"Movie {mid} ({year})", "genres": genres})
    movies_df = pd.DataFrame(movies)

    ratings = []
    for uid in range(1, NUM_USERS + 1):
        n = int(rng.integers(5, 40))
        mids = rng.choice(NUM_MOVIES, size=n, replace=False) + 1
        for i, mid in enumerate(mids):
            ratings.append({
                "userId": uid,
                "movieId": int(mid),
                "rating": float(rng.choice([1.0, 1.5, 2.0, 4.0, 4.5, 5.0])),
                "timestamp": uid * 10000 + i,
            })
    return pd.DataFrame(ratings), movies_df


class PairDataset(Dataset):
    def __init__(self, pairs: pd.DataFrame, user_map: dict, item_map: dict, item_feats: pd.DataFrame, affinities: dict) -> None:
        self.pairs = pairs
        self.user_map = user_map
        self.item_map = item_map
        self.item_feats = item_feats.set_index("movie_id")
        self.affinities = affinities

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        row = self.pairs.iloc[idx]
        uid = self.user_map[int(row["userId"])]
        iid = self.item_map[int(row["movieId"])]
        feats = self.item_feats.loc[int(row["movieId"])]
        genre_vec = torch.tensor(feats["genre_vec"], dtype=torch.float32)
        numeric = torch.tensor([feats["release_decade"], feats["log_popularity"]], dtype=torch.float32)
        aff = torch.tensor(self.affinities.get(int(row["userId"]), np.zeros(len(GENRES))), dtype=torch.float32)
        history = torch.zeros(64)
        return uid, iid, history, aff, genre_vec, numeric


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    API_ARTIFACTS.mkdir(parents=True, exist_ok=True)

    ratings, movies = generate_synthetic_data()
    popularity = ratings.groupby("movieId").size().to_dict()
    item_feats = build_item_features(movies, popularity)

    train_df, val_df, test_df = split_by_timestamp(ratings)
    for df in (train_df, val_df, test_df):
        df["label"] = df["rating"].apply(label_implicit)
        df.dropna(subset=["label"], inplace=True)
        df["label"] = df["label"].astype(int)

    users = sorted(ratings["userId"].unique())
    items = sorted(movies["movieId"].unique())
    user_map = {u: i for i, u in enumerate(users)}
    item_map = {m: i for i, m in enumerate(items)}
    inv_item_map = {i: m for m, i in item_map.items()}

    from ml.src.data.features import build_user_genre_affinity, parse_genres
    movie_genres = {int(r.movieId): parse_genres(str(r.genres)) for r in movies.itertuples()}
    affinities = build_user_genre_affinity(train_df, movies, movie_genres)

    scaler = StandardScaler()
    item_feats["log_pop_scaled"] = scaler.fit_transform(item_feats[["log_popularity"]])
    numeric_cols = ["release_decade", "log_pop_scaled"]

    model = TwoTowerModel(num_users=len(users), num_items=len(items))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    train_pairs = train_df[train_df["label"] == 1]

    dataset = PairDataset(train_pairs, user_map, item_map, item_feats, affinities)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch in loader:
            uid, iid, hist, aff, gvec, num = batch
            optimizer.zero_grad()
            user_emb, item_emb = model(uid, iid, hist, aff, gvec, num)
            logits = model.compute_logits(user_emb, item_emb)
            labels = torch.arange(len(uid))
            loss = F.cross_entropy(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/{EPOCHS} loss={total_loss / len(loader):.4f}")

    model.eval()
    all_item_ids = torch.arange(len(items))
    genre_matrix = torch.tensor(np.stack(item_feats.sort_values("movie_id")["genre_vec"].values), dtype=torch.float32)
    numeric_matrix = torch.tensor(item_feats.sort_values("movie_id")[numeric_cols].values, dtype=torch.float32)
    with torch.no_grad():
        item_embs = model.item_tower(all_item_ids, genre_matrix, numeric_matrix).numpy()

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(item_embs.astype(np.float32))

    faiss.write_index(index, str(ARTIFACTS / "faiss_index.bin"))
    with open(ARTIFACTS / "movie_id_map.json", "w") as f:
        json.dump({str(i): int(inv_item_map[i]) for i in range(len(items))}, f)

    torch.save(model.user_tower.state_dict(), ARTIFACTS / "user_tower.pt")
    torch.save(model.item_tower.state_dict(), ARTIFACTS / "item_tower.pt")

    ranker = Ranker()
    torch.save(ranker.state_dict(), ARTIFACTS / "ranker.pt")

    with open(ARTIFACTS / "genre_encoder.pkl", "wb") as f:
        pickle.dump(GENRE_TO_IDX, f)
    with open(ARTIFACTS / "feature_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    meta = {
        "num_users": len(users),
        "num_items": len(items),
        "user_map": {str(int(k)): int(v) for k, v in user_map.items()},
        "item_map": {str(int(k)): int(v) for k, v in item_map.items()},
        "embed_dim": EMBED_DIM,
        "genre_dim": len(GENRES),
    }
    with open(ARTIFACTS / "model_meta.json", "w") as f:
        json.dump(meta, f)

    # Quick eval on test
    recommended, relevant = [], []
    test_users = test_df["userId"].unique()[:200]
    for uid in test_users:
        rel = set(test_df[(test_df.userId == uid) & (test_df.label == 1)]["movieId"].astype(int))
        if not rel:
            continue
        uidx = user_map[uid]
        aff = torch.tensor(affinities.get(uid, np.zeros(len(GENRES))), dtype=torch.float32).unsqueeze(0)
        hist = torch.zeros(1, 64)
        with torch.no_grad():
            uemb = model.user_tower(torch.tensor([uidx]), hist, aff).numpy()
        _, idxs = index.search(uemb.astype(np.float32), 10)
        rec = [int(inv_item_map[i]) for i in idxs[0]]
        recommended.append(rec)
        relevant.append(rel)

    props = item_propensities({int(k): int(v) for k, v in popularity.items()})
    metrics = {
        "recall_at_10": recall_at_k(recommended, relevant, 10),
        "ndcg_at_10": ndcg_at_k(recommended, relevant, 10),
        "ips_ndcg_at_10": ips_ndcg_at_k(recommended, relevant, props, 10),
        "model_version": "demo-synthetic-v1",
    }
    with open(ARTIFACTS / "eval_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("Metrics:", metrics)

    for name in [
        "faiss_index.bin", "movie_id_map.json", "user_tower.pt", "item_tower.pt",
        "ranker.pt", "genre_encoder.pkl", "feature_scaler.pkl", "eval_metrics.json", "model_meta.json",
    ]:
        src = ARTIFACTS / name
        dst = API_ARTIFACTS / name
        if src.exists():
            dst.write_bytes(src.read_bytes())
    print(f"Artifacts copied to {API_ARTIFACTS}")


if __name__ == "__main__":
    main()
