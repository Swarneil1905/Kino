from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
GENRES = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "IMAX",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War",
]


def load_genre_encoder() -> dict[str, int]:
    path = ARTIFACTS_DIR / "genre_encoder.pkl"
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return {g: i for i, g in enumerate(GENRES)}


def genre_vector(genres: list[str], encoder: dict[str, int]) -> np.ndarray:
    vec = np.zeros(len(encoder) or len(GENRES), dtype=np.float32)
    for g in genres:
        if g in encoder:
            vec[encoder[g]] = 1.0
    return vec


def user_genre_affinity(ratings: list[tuple[list[str], int]]) -> np.ndarray:
    vec = np.zeros(len(GENRES), dtype=np.float32)
    counts = np.zeros(len(GENRES), dtype=np.float32)
    for genres, value in ratings:
        weight = 1.0 if value == 1 else -0.5
        for g in genres:
            if g in GENRE_TO_IDX:
                idx = GENRE_TO_IDX[g]
                vec[idx] += weight
                counts[idx] += 1
    counts = np.where(counts > 0, counts, 1.0)
    return (vec / counts).astype(np.float32)


GENRE_TO_IDX = {g: i for i, g in enumerate(GENRES)}


def load_model_meta() -> dict:
    path = ARTIFACTS_DIR / "model_meta.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}
