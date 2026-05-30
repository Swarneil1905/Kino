from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_optional_user
from app.ml.shadow import MODEL_VERSIONS, select_version
from app.models.impression import Impression
from app.models.user import User
from app.schemas.movie import MovieOut
from app.schemas.recommendation import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


async def _log_impressions(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    movie_ids: list[int],
    model_version: str,
) -> None:
    """Fire-and-forget: insert one impression row per movie position."""
    now = datetime.now(timezone.utc)
    rows = [
        Impression(
            user_id=user_id,
            movie_id=mid,
            position=pos,
            model_version=model_version,
            shown_at=now,
        )
        for pos, mid in enumerate(movie_ids)
    ]
    db.add_all(rows)
    try:
        await db.commit()
    except Exception:
        await db.rollback()


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationResponse:
    engine = request.app.state.recommendation_engine
    user_id = user.id if user else None

    # Shadow deployment: select model variant for this request
    version = select_version() if user_id else "v1-baseline"
    lam = MODEL_VERSIONS[version]["mmr_lambda"]

    movies, cache_hit, computed_at = await engine.recommend(
        db, user_id, limit=limit, mmr_lambda=lam
    )

    # Log impressions asynchronously — do not block the response
    if user_id and movies:
        asyncio.ensure_future(
            _log_impressions(db, user_id, [m.id for m in movies], version)
        )

    return RecommendationResponse(
        movies=movies,
        cache_hit=cache_hit,
        computed_at=computed_at,
        model_version=version,
    )


@router.get("/cold-start")
async def cold_start_recommendations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    genres: str = Query(..., description="Comma-separated genre names"),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, list[MovieOut]]:
    engine = request.app.state.recommendation_engine
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    movies = await engine.cold_start(db, genre_list, limit=limit)
    return {"movies": movies}


@router.get("/similar/{movie_id}")
async def similar_movies(
    movie_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, list[MovieOut]]:
    engine = request.app.state.recommendation_engine
    movies = await engine.similar(db, movie_id, limit=limit)
    return {"movies": movies}


@router.post("/refresh", response_model=RecommendationResponse)
async def refresh_recommendations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationResponse:
    engine = request.app.state.recommendation_engine
    version = select_version()
    lam = MODEL_VERSIONS[version]["mmr_lambda"]
    movies, cache_hit, computed_at = await engine.recommend(
        db, user.id, limit=limit, force_refresh=True, mmr_lambda=lam
    )
    if movies:
        asyncio.ensure_future(
            _log_impressions(db, user.id, [m.id for m in movies], version)
        )
    return RecommendationResponse(
        movies=movies,
        cache_hit=cache_hit,
        computed_at=computed_at,
        model_version=version,
    )


@router.post("/click/{movie_id}")
async def record_click(
    movie_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, str]:
    """Mark the most recent impression for this user+movie as clicked.

    Called by the frontend when a user navigates to a movie detail page
    that was shown in a recommendation row.
    """
    if not user:
        return {"status": "skipped"}

    from sqlalchemy import select, desc
    result = await db.execute(
        select(Impression)
        .where(Impression.user_id == user.id, Impression.movie_id == movie_id, Impression.clicked.is_(False))
        .order_by(desc(Impression.shown_at))
        .limit(1)
    )
    impression = result.scalar_one_or_none()
    if impression:
        impression.clicked = True
        impression.clicked_at = datetime.now(timezone.utc)
        await db.commit()
    return {"status": "ok"}
