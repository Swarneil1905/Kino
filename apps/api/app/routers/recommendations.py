from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_optional_user
from app.models.user import User
from app.schemas.movie import MovieOut
from app.schemas.recommendation import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationResponse:
    engine = request.app.state.recommendation_engine
    user_id = user.id if user else None
    movies, cache_hit, computed_at = await engine.recommend(db, user_id, limit=limit)
    return RecommendationResponse(movies=movies, cache_hit=cache_hit, computed_at=computed_at)


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
    movies, cache_hit, computed_at = await engine.recommend(db, user.id, limit=limit, force_refresh=True)
    return RecommendationResponse(movies=movies, cache_hit=cache_hit, computed_at=computed_at)
