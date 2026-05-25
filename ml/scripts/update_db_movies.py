#!/usr/bin/env python3
"""
Upsert all movies from movielens_seed_data.json into the Postgres movies table.
Run AFTER fetch_tmdb_metadata.py and train_real_movielens.py.

Run from kino root:
    python ml/scripts/update_db_movies.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT      = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "apps" / "api" / "app" / "scripts" / "movielens_seed_data.json"

# Matches docker-compose postgres service
DB_DSN = "host=localhost port=5432 dbname=kino user=postgres password=postgres"


def main():
    records = json.loads(SEED_PATH.read_text())
    print(f"Upserting {len(records)} movies into DB …")

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur  = conn.cursor()

    sql = """
        INSERT INTO movies (
            id, tmdb_id, title, overview,
            poster_path, backdrop_path,
            release_year, runtime_minutes, maturity_rating,
            vote_average, genres, popularity_score
        ) VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            title           = EXCLUDED.title,
            overview        = EXCLUDED.overview,
            poster_path     = EXCLUDED.poster_path,
            backdrop_path   = EXCLUDED.backdrop_path,
            release_year    = EXCLUDED.release_year,
            runtime_minutes = EXCLUDED.runtime_minutes,
            maturity_rating = EXCLUDED.maturity_rating,
            vote_average    = EXCLUDED.vote_average,
            genres          = EXCLUDED.genres,
            popularity_score= EXCLUDED.popularity_score
    """

    rows = []
    for r in records:
        rows.append((
            r["id"],
            10_000_000 + r["id"],     # synthetic tmdb_id (won't clash with real TMDB IDs)
            r["title"],
            r.get("overview", ""),
            r.get("poster_path"),
            r.get("backdrop_path"),
            r.get("release_year", 2000),
            r.get("runtime_minutes", 110),
            r.get("maturity_rating", "PG-13"),
            float(r.get("vote_average", 7.0)),
            r.get("genres", ["Drama"]),
            float(r.get("popularity_score", 500.0)),
        ))

    psycopg2.extras.execute_values(cur, sql, rows, page_size=500)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Done — {len(rows)} movies upserted.")


if __name__ == "__main__":
    main()
