"""User and item feature construction for two-tower training."""

from __future__ import annotations

import numpy as np
import pandas as pd

GENRES = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "IMAX",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War",
]
GENRE_TO_IDX = {g: i for i, g in enumerate(GENRES)}


def parse_genres(genre_str: str) -> list[str]:
    if not genre_str or genre_str == "(no genres listed)":
        return []
    return [g.strip() for g in genre_str.split("|") if g.strip() in GENRE_TO_IDX]


def genre_multi_hot(genres: list[str]) -> np.ndarray:
    vec = np.zeros(len(GENRES), dtype=np.float32)
    for g in genres:
        if g in GENRE_TO_IDX:
            vec[GENRE_TO_IDX[g]] = 1.0
    return vec


def release_decade(year: int | float) -> float:
    if pd.isna(year) or year <= 0:
        return 0.5
    return float(np.clip((float(year) - 1920) / 110.0, 0.0, 1.0))


def log_popularity(pop: float) -> float:
    return float(np.log1p(max(pop, 0.0)))


def build_item_features(movies: pd.DataFrame, popularity: dict[int, float]) -> pd.DataFrame:
    rows = []
    for _, row in movies.iterrows():
        mid = int(row["movieId"])
        genres = parse_genres(str(row.get("genres", "")))
        year = int(str(row.get("title", ""))[-5:-1]) if "(" in str(row.get("title", "")) else 2000
        rows.append({
            "movie_id": mid,
            "genres": genres,
            "genre_vec": genre_multi_hot(genres),
            "release_decade": release_decade(year),
            "log_popularity": log_popularity(popularity.get(mid, 1.0)),
        })
    return pd.DataFrame(rows)


def build_user_genre_affinity(
    ratings: pd.DataFrame,
    movies: pd.DataFrame,
    movie_genres: dict[int, list[str]],
) -> dict[int, np.ndarray]:
    movie_title = movies.set_index("movieId")["title"].to_dict()
    affinities: dict[int, np.ndarray] = {}
    for uid, group in ratings.groupby("userId"):
        vec = np.zeros(len(GENRES), dtype=np.float32)
        counts = np.zeros(len(GENRES), dtype=np.float32)
        for _, r in group.iterrows():
            mid = int(r["movieId"])
            genres = movie_genres.get(mid, parse_genres(str(movies.loc[movies.movieId == mid, "genres"].iloc[0]) if mid in movies.movieId.values else ""))
            weight = 1.0 if r["rating"] >= 4.0 else -0.5 if r["rating"] < 2.5 else 0.0
            if weight == 0:
                continue
            for g in genres:
                if g in GENRE_TO_IDX:
                    idx = GENRE_TO_IDX[g]
                    vec[idx] += weight
                    counts[idx] += 1
        counts = np.where(counts > 0, counts, 1.0)
        affinities[int(uid)] = (vec / counts).astype(np.float32)
    return affinities
