#!/usr/bin/env python3
"""
Generate movielens_seed_data.json for the API seed script.

Run from kino root:
    python ml/scripts/export_seed_data.py

Reads:
    apps/api/app/artifacts/movie_id_map.json  (FAISS pos -> MovieLens ID)
    ml/data/movies.csv                         (MovieLens titles + genres)

Writes:
    apps/api/app/scripts/movielens_seed_data.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MAP_PATH   = ROOT / "apps" / "api" / "app" / "artifacts" / "movie_id_map.json"
MOVIES_CSV = ROOT / "ml" / "data" / "movies.csv"
OUT_PATH   = ROOT / "apps" / "api" / "app" / "scripts" / "movielens_seed_data.json"

# Genre normalization: MovieLens uses pipe-separated genre strings
ML_GENRE_MAP = {
    "Action":      "Action",
    "Adventure":   "Adventure",
    "Animation":   "Animation",
    "Children's":  "Family",
    "Children":    "Family",
    "Comedy":      "Comedy",
    "Crime":       "Crime",
    "Documentary": "Documentary",
    "Drama":       "Drama",
    "Fantasy":     "Fantasy",
    "Film-Noir":   "Thriller",
    "Horror":      "Horror",
    "Musical":     "Musical",
    "Mystery":     "Mystery",
    "Romance":     "Romance",
    "Sci-Fi":      "Sci-Fi",
    "Thriller":    "Thriller",
    "War":         "War",
    "Western":     "Western",
    "(no genres listed)": "Drama",
}

def parse_year(title: str) -> tuple[str, int | None]:
    """Extract year from 'Title (YYYY)' format."""
    if title.endswith(")") and len(title) > 6:
        try:
            year = int(title[-5:-1])
            if 1880 <= year <= 2030:
                return title[:-7].strip(), year
        except ValueError:
            pass
    return title.strip(), None


def main() -> None:
    # Load MovieLens IDs that are in our FAISS index
    raw_map = json.loads(MAP_PATH.read_text())
    ml_ids = {int(v) for v in raw_map.values()}
    print(f"MovieLens IDs needed: {len(ml_ids)}")

    # Parse movies.csv
    movie_lookup: dict[int, dict] = {}
    with MOVIES_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row["movieId"])
            if mid not in ml_ids:
                continue
            title, year = parse_year(row["title"])
            genres_raw = row.get("genres", "Drama").split("|")
            genres = list(dict.fromkeys(
                ML_GENRE_MAP.get(g, "Drama") for g in genres_raw
            ))[:3]  # keep max 3 genres
            movie_lookup[mid] = {
                "title": title,
                "release_year": year or 2000,
                "genres": genres,
            }

    print(f"Found in movies.csv: {len(movie_lookup)}")

    # Build seed records — one per MovieLens ID
    records: list[dict] = []
    for ml_id in sorted(ml_ids):
        info = movie_lookup.get(ml_id, {
            "title": f"Movie #{ml_id}",
            "release_year": 2000,
            "genres": ["Drama"],
        })
        records.append({
            "id": ml_id,
            "title": info["title"],
            "release_year": info["release_year"],
            "genres": info["genres"],
            # Placeholder fields (can be enriched with TMDB later)
            "overview": f"{info['title']} — a film from the MovieLens catalog.",
            "poster_path": None,
            "backdrop_path": None,
            "vote_average": 7.0,
            "maturity_rating": "PG-13",
            "runtime_minutes": 110,
            "popularity_score": 1000.0 / (1 + sorted(ml_ids).index(ml_id)),
        })

    OUT_PATH.write_text(json.dumps(records, indent=2))
    print(f"Written {len(records)} movies to {OUT_PATH}")


if __name__ == "__main__":
    main()
