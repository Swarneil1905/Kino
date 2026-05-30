from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import numpy as np
import torch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import delete_cache, get_cache, set_cache

logger = logging.getLogger(__name__)
from app.ml.diversity import mmr_rerank
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
        # Pre-extracted item embeddings for MMR diversity reranking
        # {movie_id: L2-normalised embedding vector}
        self.item_embeddings: dict[int, np.ndarray] = {}

    def load(self) -> None:
        self.genre_encoder = load_genre_encoder()
        self.meta = load_model_meta()
        faiss_ok = self.faiss.load()

        # Pre-extract all item embeddings from the FAISS index so MMR can
        # compute pairwise cosine similarity without hitting the index repeatedly.
        if faiss_ok and self.faiss.index is not None:
            raw = self.faiss.index.reconstruct_n(0, self.faiss.index.ntotal)
            self.item_embeddings = {
                self.faiss.movie_id_map[pos]: raw[pos]
                for pos in range(self.faiss.index.ntotal)
            }
            logger.info("[ENGINE] Pre-extracted %d item embeddings for MMR", len(self.item_embeddings))

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
        mmr_lambda: float = 0.7,
    ) -> tuple[list[MovieOut], bool, datetime]:
        now = datetime.now(timezone.utc)
        cache_key = f"rec:{user_id}" if user_id else None

        if cache_key and not force_refresh:
            cached = await get_cache(cache_key)
            if cached:
                ids = json.loads(cached)
                logger.info("[REC] Cache HIT for %s — cached ids count: %d, returning: %d", cache_key, len(ids), min(len(ids), limit))
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
        faiss_results = self.faiss.search(embedding, k=200)
        candidates = [mid for mid in faiss_results if mid not in rated_ids]
        logger.info("[REC] user=%s | FAISS returned: %d | after rated filter: %d candidates", user_id, len(faiss_results), len(candidates))

        # Step 1: Ranker scores candidates and returns a larger pool for MMR to work with.
        # We ask for limit*3 (e.g. 30 for limit=10) so MMR has room to pick diverse items.
        mmr_pool_size = min(len(candidates), limit * 3)
        if self.ranker and self.item_tower and candidates:
            pre_ranked = await self._rerank(db, embedding, candidates, mmr_pool_size)
        else:
            pre_ranked = candidates[:mmr_pool_size]

        # Step 2: MMR diversity reranking — picks the final `limit` items that
        # balance relevance (position in pre_ranked) vs novelty (cosine distance).
        if self.item_embeddings and len(pre_ranked) > limit:
            rel_scores = {mid: 1.0 / (i + 1) for i, mid in enumerate(pre_ranked)}
            ranked_ids = mmr_rerank(
                candidates=pre_ranked,
                item_embeddings=self.item_embeddings,
                relevance_scores=rel_scores,
                k=limit,
                lam=mmr_lambda,
            )
            logger.info("[MMR] user=%s | lambda=%.2f | pool: %d → diverse top: %d", user_id, mmr_lambda, len(pre_ranked), len(ranked_ids))
        else:
            ranked_ids = pre_ranked[:limit]

        logger.info("[REC] user=%s | final ranked_ids count: %d", user_id, len(ranked_ids))
        movies = await self._fetch_movies(db, ranked_ids)
        logger.info("[REC] user=%s | movies fetched from DB: %d", user_id, len(movies))
        if cache_key:
            await set_cache(cache_key, json.dumps(ranked_ids), ttl=900)
        return movies, False, now

    async def cold_start(
        self,
        db: AsyncSession,
        genre_names: list[str],
        limit: int = 20,
    ) -> list[MovieOut]:
        """Recommend movies for a brand-new user using only genre preferences.

        Instead of a learned user embedding, we build a genre affinity vector
        from the genres the user selected during onboarding, then run it through
        the UserTower with a neutral user ID (0) and zero history.

        This gives meaningful personalisation before the user has rated anything.
        """
        if not self.loaded or not self.user_tower:
            return await self._popular_movies(db, limit)

        # Build an 18-dim genre affinity vector: 1.0 for each chosen genre
        aff = np.zeros(len(self.genre_encoder), dtype=np.float32)
        for g in genre_names:
            idx = self.genre_encoder.get(g)
            if idx is not None:
                aff[idx] = 1.0

        if aff.sum() == 0:
            # No recognisable genres — fall back to popular
            return await self._popular_movies(db, limit)

        with torch.no_grad():
            emb = self.user_tower(
                torch.tensor([0]),           # neutral user ID
                torch.zeros(1, 64),          # no watch history
                torch.tensor(aff).unsqueeze(0),
            )
        embedding = emb.numpy()[0].astype(np.float32)

        faiss_results = self.faiss.search(embedding, k=min(limit * 3, 200))

        # Apply MMR so the starter list is diverse across the chosen genres
        if self.item_embeddings and len(faiss_results) > limit:
            rel_scores = {mid: 1.0 / (i + 1) for i, mid in enumerate(faiss_results)}
            candidates = mmr_rerank(
                candidates=faiss_results,
                item_embeddings=self.item_embeddings,
                relevance_scores=rel_scores,
                k=limit,
                lam=0.7,
            )
        else:
            candidates = faiss_results[:limit]

        logger.info(
            "[COLD-START] genres=%s | FAISS=%d | MMR→%d",
            genre_names, len(faiss_results), len(candidates),
        )
        return await self._fetch_movies(db, candidates)

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

        logger.info("[RERANK] candidates in: %d | scored: %d | returning top: %d", len(candidates), len(scores), limit)
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
