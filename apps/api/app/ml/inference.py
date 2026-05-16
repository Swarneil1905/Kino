from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import numpy as np
import torch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import delete_cache, get_cache, set_cache
from app.ml.faiss_store import FaissStore
from app.ml.features import GENRE_TO_IDX, genre_vector, load_genre_encoder, load_model_meta, user_genre_affinity
from app.ml.item_tower import ItemTower
from app.ml.ranker import Ranker
from app.ml.user_tower import UserTower
from app.models.movie import Movie
from app.models.rating import Rating
from app.schemas.movie import MovieOut, movie_to_schema

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


class RecommendationEngine:
    def __init__(self) -> None:
        self.loaded = False
        self.faiss = FaissStore()
        self.meta: dict = {}
        self.user_tower: UserTower | None = None
        self.item_tower: ItemTower | None = None
        self.ranker: Ranker | None = None
        self.genre_encoder: dict[str, int] = {}
        self.device = torch.device("cpu")

    def load(self) -> None:
        self.genre_encoder = load_genre_encoder()
        self.meta = load_model_meta()
        faiss_ok = self.faiss.load()

        if (ARTIFACTS_DIR / "user_tower.pt").exists() and self.meta:
            num_users = int(self.meta.get("num_users", 1))
            num_items = int(self.meta.get("num_items", 1))
            genre_dim = int(self.meta.get("genre_dim", 18))
            embed_dim = int(self.meta.get("embed_dim", 128))

            self.user_tower = UserTower(num_users, genre_dim, embed_dim)
            self.item_tower = ItemTower(num_items, genre_dim, embed_dim)
            self.ranker = Ranker()

            self.user_tower.load_state_dict(torch.load(ARTIFACTS_DIR / "user_tower.pt", map_location="cpu"))
            self.item_tower.load_state_dict(torch.load(ARTIFACTS_DIR / "item_tower.pt", map_location="cpu"))
            if (ARTIFACTS_DIR / "ranker.pt").exists():
                self.ranker.load_state_dict(torch.load(ARTIFACTS_DIR / "ranker.pt", map_location="cpu"))

            self.user_tower.eval()
            self.item_tower.eval()
            self.ranker.eval()

        self.loaded = faiss_ok and self.user_tower is not None

    def _user_idx(self, user_id: UUID) -> int:
        user_map = self.meta.get("user_map", {})
        return int(user_map.get(str(hash(user_id) % int(self.meta.get("num_users", 1))), 0)) % int(self.meta.get("num_users", 1))

    async def _embed_user(self, db: AsyncSession, user_id: UUID) -> np.ndarray | None:
        if not self.user_tower:
            return None

        result = await db.execute(
            select(Rating, Movie).join(Movie, Movie.id == Rating.movie_id).where(Rating.user_id == user_id)
        )
        rows = result.all()
        if not rows:
            return None

        rating_feats = [(list(m.genres or []), r.value) for r, m in rows]
        aff = user_genre_affinity(rating_feats)
        uidx = self._user_idx(user_id)

        with torch.no_grad():
            emb = self.user_tower(
                torch.tensor([uidx]),
                torch.zeros(1, 64),
                torch.tensor(aff).unsqueeze(0),
            )
        return emb.numpy()[0]

    async def recommend(
        self,
        db: AsyncSession,
        user_id: UUID | None,
        limit: int = 20,
        force_refresh: bool = False,
    ) -> tuple[list[MovieOut], bool, datetime]:
        now = datetime.now(timezone.utc)
        cache_key = f"rec:{user_id}" if user_id else None

        if cache_key and not force_refresh:
            cached = await get_cache(cache_key)
            if cached:
                ids = json.loads(cached)
                movies = await self._fetch_movies(db, ids[:limit])
                return movies, True, now

        if user_id is None or not self.loaded:
            movies = await self._popular_movies(db, limit)
            return movies, False, now

        emb_key = f"emb:{user_id}"
        embedding = None
        if not force_refresh:
            cached_emb = await get_cache(emb_key)
            if cached_emb:
                embedding = np.frombuffer(bytes.fromhex(cached_emb), dtype=np.float32)

        if embedding is None:
            embedding = await self._embed_user(db, user_id)
            if embedding is not None:
                await set_cache(emb_key, embedding.astype(np.float32).tobytes().hex(), ttl=3600)

        if embedding is None:
            movies = await self._popular_movies(db, limit)
            return movies, False, now

        rated_ids = await self._rated_movie_ids(db, user_id)
        candidates = [mid for mid in self.faiss.search(embedding, k=200) if mid not in rated_ids]
        ranked_ids = candidates[:limit]

        if self.ranker and self.item_tower and candidates:
            ranked_ids = await self._rerank(db, embedding, candidates, limit)

        movies = await self._fetch_movies(db, ranked_ids)
        if cache_key:
            await set_cache(cache_key, json.dumps(ranked_ids), ttl=900)
        return movies, False, now

    async def similar(self, db: AsyncSession, movie_id: int, limit: int = 10) -> list[MovieOut]:
        if not self.loaded or not self.item_tower:
            source = await db.get(Movie, movie_id)
            query = select(Movie).where(Movie.id != movie_id)
            if source and source.genres:
                query = query.where(Movie.genres.overlap(source.genres))
            result = await db.execute(query.order_by(Movie.popularity_score.desc().nullslast()).limit(limit))
            return [movie_to_schema(m) for m in result.scalars().all()]

        item_map = self.meta.get("item_map", {})
        iidx = int(item_map.get(str(movie_id), movie_id % int(self.meta.get("num_items", 1))))

        movie = await db.get(Movie, movie_id)
        if not movie:
            return []

        gvec = genre_vector(list(movie.genres or []), self.genre_encoder)
        decade = ((movie.release_year or 2000) - 1920) / 110.0
        pop = float(np.log1p(float(movie.popularity_score or 1.0)))

        with torch.no_grad():
            item_emb = self.item_tower(
                torch.tensor([iidx]),
                torch.tensor(gvec).unsqueeze(0),
                torch.tensor([[decade, pop]]),
            ).numpy()[0]

        ids = self.faiss.search(item_emb, k=limit + 1)
        ids = [i for i in ids if i != movie_id][:limit]
        return await self._fetch_movies(db, ids)

    async def _rerank(self, db: AsyncSession, user_emb_np: np.ndarray, candidates: list[int], limit: int) -> list[int]:
        assert self.ranker and self.item_tower
        item_map = self.meta.get("item_map", {})
        scores: list[tuple[int, float]] = []

        user_t = torch.tensor(user_emb_np).unsqueeze(0)
        for mid in candidates:
            iidx = int(item_map.get(str(mid), mid % int(self.meta.get("num_items", 1))))
            movie = await db.get(Movie, mid)
            if not movie:
                continue
            gvec = genre_vector(list(movie.genres or []), self.genre_encoder)
            decade = ((movie.release_year or 2000) - 1920) / 110.0
            pop = float(np.log1p(float(movie.popularity_score or 1.0)))
            primary_genre = (movie.genres or ["Drama"])[0]
            gscore = float(user_emb_np[GENRE_TO_IDX.get(primary_genre, 0)] if primary_genre in GENRE_TO_IDX else 0)

            with torch.no_grad():
                item_emb = self.item_tower(
                    torch.tensor([iidx]),
                    torch.tensor(gvec).unsqueeze(0),
                    torch.tensor([[decade, pop]]),
                )
                score = self.ranker(user_t, item_emb, torch.tensor([gscore]), torch.tensor([pop]), torch.tensor([decade]))
            scores.append((mid, float(score.item())))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [mid for mid, _ in scores[:limit]]

    async def _rated_movie_ids(self, db: AsyncSession, user_id: UUID) -> set[int]:
        result = await db.execute(select(Rating.movie_id).where(Rating.user_id == user_id))
        return {int(r[0]) for r in result.all()}

    async def _fetch_movies(self, db: AsyncSession, ids: list[int]) -> list[MovieOut]:
        if not ids:
            return []
        result = await db.execute(select(Movie).where(Movie.id.in_(ids)))
        by_id = {m.id: m for m in result.scalars().all()}
        return [movie_to_schema(by_id[i], match_percent=85 + (i % 14)) for i in ids if i in by_id]

    async def _popular_movies(self, db: AsyncSession, limit: int) -> list[MovieOut]:
        result = await db.execute(select(Movie).order_by(Movie.popularity_score.desc().nullslast()).limit(limit))
        return [movie_to_schema(m, match_percent=80 + idx % 15) for idx, m in enumerate(result.scalars().all())]

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        await delete_cache(f"rec:{user_id}")
        await delete_cache(f"emb:{user_id}")
