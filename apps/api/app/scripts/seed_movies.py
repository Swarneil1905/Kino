"""Seed movies table with catalog data aligned to ML artifact IDs."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

CURATED: dict[int, dict] = {
    1: {"title": "The Matrix", "overview": "A hacker discovers the truth about reality.", "release_year": 1999, "genres": ["Sci-Fi", "Action"], "poster_path": "/p96K82GE3v2dO1LOgg6m6kSh6b7.jpg", "backdrop_path": "/bV9qTV7VLoCTghvMEsJrz2YgrrO.jpg", "vote_average": 8.7, "maturity_rating": "R", "runtime_minutes": 136},
    2: {"title": "Arrival", "overview": "A linguist races to communicate with alien visitors.", "release_year": 2016, "genres": ["Sci-Fi", "Drama"], "poster_path": "/x2FJsfBzzY3jhGB42SUCO15RX5v.jpg", "backdrop_path": "/8uO0gUM2dJiykgV0zDPavjl27wQ.jpg", "vote_average": 7.9, "maturity_rating": "PG-13", "runtime_minutes": 116},
    3: {"title": "Parasite", "overview": "Class tension erupts inside an elegant modern home.", "release_year": 2019, "genres": ["Thriller", "Drama"], "poster_path": "/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", "backdrop_path": "/TU9NIjwzjoKPwQHoHshkFcQUCG.jpg", "vote_average": 8.5, "maturity_rating": "R", "runtime_minutes": 132},
    4: {"title": "Mad Max: Fury Road", "overview": "A desert chase becomes a fight for survival.", "release_year": 2015, "genres": ["Action"], "poster_path": "/8hDU8iwne3t8pQp0MJaqYCzzM8.jpg", "backdrop_path": "/tbhdm8UJAb4ViCTsEYHZXJ5AlAI.jpg", "vote_average": 8.1, "maturity_rating": "R", "runtime_minutes": 120},
    5: {"title": "Spirited Away", "overview": "A girl enters a spirit world to save her parents.", "release_year": 2001, "genres": ["Animation", "Fantasy"], "poster_path": "/39wmItIWsg5sZMyRU9kQwcQQ03g.jpg", "backdrop_path": "/Ab8mkf9jc8xqjXAB8Jq8S4Lo0h.jpg", "vote_average": 8.6, "maturity_rating": "PG", "runtime_minutes": 125},
    6: {"title": "The Social Network", "overview": "Ambition and betrayal surround Facebook's founding.", "release_year": 2010, "genres": ["Drama"], "poster_path": "/ok5Q8JHs6r52P0WmzgP9XqM6fWq.jpg", "backdrop_path": "/6j3e7VvUyO4o0o6m4m4m4m4m4m4.jpg", "vote_average": 7.8, "maturity_rating": "PG-13", "runtime_minutes": 120},
    7: {"title": "Inception", "overview": "A thief enters dreams to plant an idea.", "release_year": 2010, "genres": ["Sci-Fi", "Action"], "poster_path": "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg", "backdrop_path": "/s3TBrRGB1iav7gFOCNx3HmkMmMO.jpg", "vote_average": 8.8, "maturity_rating": "PG-13", "runtime_minutes": 148},
    8: {"title": "Interstellar", "overview": "Explorers travel through a wormhole to save humanity.", "release_year": 2014, "genres": ["Sci-Fi", "Drama"], "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "backdrop_path": "/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg", "vote_average": 8.6, "maturity_rating": "PG-13", "runtime_minutes": 169},
    9: {"title": "The Dark Knight", "overview": "Batman faces the Joker in Gotham.", "release_year": 2008, "genres": ["Action", "Crime"], "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "backdrop_path": "/nMKdUUzpRpqztF7uoD69ubWBG7f.jpg", "vote_average": 9.0, "maturity_rating": "PG-13", "runtime_minutes": 152},
    10: {"title": "Pulp Fiction", "overview": "Intersecting crime stories in Los Angeles.", "release_year": 1994, "genres": ["Crime", "Drama"], "poster_path": "/d5iIlFn5s0ImszYzBPb8JPI66DQ.jpg", "backdrop_path": "/suaEOtk1NhoeR3tQ6GSpMpRxdqL.jpg", "vote_average": 8.9, "maturity_rating": "R", "runtime_minutes": 154},
}


async def seed_movies(session: AsyncSession, max_movies: int = 200) -> int:
    count_result = await session.execute(select(func.count()).select_from(Movie))
    if int(count_result.scalar_one()) > 0:
        return 0

    movies: list[dict] = []
    map_path = ARTIFACTS / "movie_id_map.json"
    max_id = max_movies
    if map_path.exists():
        raw = json.loads(map_path.read_text())
        max_id = min(max_movies, max(int(v) for v in raw.values()))

    for mid in range(1, max_id + 1):
        if mid in CURATED:
            data = CURATED[mid]
        else:
            year = 1985 + (mid % 35)
            genres = [["Action"], ["Drama"], ["Comedy"], ["Sci-Fi"], ["Thriller"]][mid % 5]
            data = {
                "title": f"Kino Pick {mid}",
                "overview": f"A compelling story from the Kino catalog (#{mid}).",
                "release_year": year,
                "genres": genres,
                "poster_path": None,
                "backdrop_path": None,
                "vote_average": 7.0 + (mid % 20) / 10,
                "maturity_rating": "PG-13",
                "runtime_minutes": 110 + (mid % 40),
            }
        movies.append({
            "id": mid,
            "tmdb_id": 10000 + mid,
            "title": data["title"],
            "overview": data["overview"],
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "release_year": data["release_year"],
            "runtime_minutes": data.get("runtime_minutes", 120),
            "maturity_rating": data.get("maturity_rating", "PG-13"),
            "vote_average": data.get("vote_average", 7.5),
            "genres": data["genres"],
            "popularity_score": float(1000 - mid),
        })

    stmt = insert(Movie).values(movies)
    stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
    await session.execute(stmt)
    await session.commit()
    return len(movies)
