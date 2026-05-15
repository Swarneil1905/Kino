from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingIn, RatingOut, RatingsListOut

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", response_model=RatingOut)
async def submit_rating(
    payload: RatingIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> RatingOut:
    movie = await db.get(Movie, payload.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    result = await db.execute(
        select(Rating).where(Rating.user_id == user.id, Rating.movie_id == payload.movie_id)
    )
    existing = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if payload.value is None:
        if existing:
            await db.delete(existing)
        await db.commit()
        await request.app.state.recommendation_engine.invalidate_user_cache(user.id)
        return RatingOut(movie_id=payload.movie_id, value=None, updated_at=now)

    if payload.value not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1, -1, or null")

    if existing:
        existing.value = payload.value
    else:
        db.add(Rating(user_id=user.id, movie_id=payload.movie_id, value=payload.value))

    await db.commit()
    await request.app.state.recommendation_engine.invalidate_user_cache(user.id)
    return RatingOut(movie_id=payload.movie_id, value=payload.value, updated_at=now)


@router.get("/me", response_model=RatingsListOut)
async def my_ratings(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RatingsListOut:
    result = await db.execute(select(Rating).where(Rating.user_id == user.id))
    ratings = [
        RatingOut(movie_id=r.movie_id, value=r.value, updated_at=r.created_at)
        for r in result.scalars().all()
    ]
    return RatingsListOut(ratings=ratings)
