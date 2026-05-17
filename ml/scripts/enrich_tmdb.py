#!/usr/bin/env python3
"""
Enrich movielens_seed_data.json with real TMDB poster/backdrop images.

Run from kino root:
    python ml/scripts/enrich_tmdb.py

Reads:  apps/api/app/scripts/movielens_seed_data.json
Writes: apps/api/app/scripts/movielens_seed_data.json  (in-place, with images)

Also writes a summary of matches to: ml/artifacts/tmdb_match_report.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "apps" / "api" / "app" / "scripts" / "movielens_seed_data.json"
REPORT_PATH = ROOT / "ml" / "artifacts" / "tmdb_match_report.json"

def _load_env(path: Path) -> dict[str, str]:
    """Minimal .env parser — no extra dependencies needed."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result

_env = _load_env(ROOT / "apps" / "web" / ".env")
TMDB_TOKEN = _env.get("TMDB_READ_TOKEN", "")
if not TMDB_TOKEN:
    raise SystemExit(
        "Error: TMDB_READ_TOKEN not found in apps/web/.env\n"
        "Add this line to that file:\n"
        "  TMDB_READ_TOKEN=<your_read_access_token>"
    )
TMDB_BASE = "https://api.themoviedb.org/3"


def tmdb_get(path: str, params: dict) -> dict:
    url = f"{TMDB_BASE}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TMDB_TOKEN}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def search_movie(title: str, year: int | None) -> dict | None:
    """Search TMDB and return the best-matching result, or None."""
    params: dict = {"query": title, "include_adult": "false", "language": "en-US", "page": 1}
    if year:
        params["year"] = year

    try:
        data = tmdb_get("/search/movie", params)
    except Exception:
        return None

    results = data.get("results", [])
    if not results:
        # Retry without year constraint
        if year:
            params.pop("year", None)
            try:
                data = tmdb_get("/search/movie", params)
                results = data.get("results", [])
            except Exception:
                return None

    if not results:
        return None

    # Prefer exact title match, then fall back to first result
    title_lower = title.lower()
    for r in results:
        if r.get("title", "").lower() == title_lower:
            return r
    return results[0]


def main() -> None:
    records: list[dict] = json.loads(SEED_PATH.read_text())
    print(f"Enriching {len(records)} movies with TMDB images...")

    matched = 0
    skipped = 0
    failed = 0
    report: list[dict] = []

    for i, rec in enumerate(records):
        title = rec["title"]
        year = rec.get("release_year")

        result = search_movie(title, year)

        if result:
            poster = result.get("poster_path")
            backdrop = result.get("backdrop_path")
            overview = result.get("overview") or rec.get("overview", "")
            vote = result.get("vote_average")

            rec["poster_path"] = poster
            rec["backdrop_path"] = backdrop
            if overview:
                rec["overview"] = overview
            if vote:
                rec["vote_average"] = round(float(vote), 1)

            matched += 1
            report.append({"id": rec["id"], "title": title, "tmdb_title": result.get("title"), "matched": True})
        else:
            skipped += 1
            report.append({"id": rec["id"], "title": title, "matched": False})

        # Progress every 50 movies
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(records)} — matched {matched}, skipped {skipped}")

        # Respect TMDB rate limit (40 requests/10s)
        time.sleep(0.28)

    SEED_PATH.write_text(json.dumps(records, indent=2))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    print(f"\nDone — {matched} matched, {skipped} not found, {failed} errors")
    print(f"Seed data updated: {SEED_PATH}")
    print(f"Match report: {REPORT_PATH}")
    print(f"\nNext steps:")
    print(f"  docker compose down -v")
    print(f"  docker compose up -d --build")


if __name__ == "__main__":
    main()
