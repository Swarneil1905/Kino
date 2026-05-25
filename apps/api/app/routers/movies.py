from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieListOut, MovieOut, movie_to_schema

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MovieListOut)
async def list_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    genre: str | None = None,
    year: int | None = None,
) -> MovieListOut:
    query = select(Movie)
    if genre:
        query = query.where(Movie.genres.contains([genre]))
    if year:
        query = query.where(Movie.release_year == year)

    count_query = select(func.count()).select_from(Movie)
    if genre:
        count_query = count_query.where(Movie.genres.contains([genre]))
    if year:
        count_query = count_query.where(Movie.release_year == year)
    total = int((await db.execute(count_query)).scalar_one())

    result = await db.execute(query.order_by(Movie.popularity_score.desc().nullslast()).offset((page - 1) * limit).limit(limit))
    items = [movie_to_schema(m) for m in result.scalars().all()]
    return MovieListOut(items=items, total=total, page=page)


@router.get("/trending")
async def trending_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=30, ge=1, le=50),
) -> dict[str, list[MovieOut]]:
    """Top movies ranked by popularity score."""
    result = await db.execute(
        select(Movie).order_by(Movie.popularity_score.desc().nullslast()).limit(limit)
    )
    return {"movies": [movie_to_schema(m) for m in result.scalars().all()]}


@router.get("/top-rated")
async def top_rated_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=20),
) -> dict[str, list[MovieOut]]:
    """Top movies ranked by vote average (shown as Top 10 row)."""
    result = await db.execute(
        select(Movie)
        .where(Movie.vote_average.isnot(None))
        .order_by(Movie.vote_average.desc())
        .limit(limit)
    )
    return {"movies": [movie_to_schema(m) for m in result.scalars().all()]}


@router.get("/search")
async def search_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(min_length=2),
    limit: int = Query(default=20, le=50),
) -> dict[str, list[MovieOut]]:
    pattern = f"%{q}%"
    result = await db.execute(
        select(Movie).where(or_(Movie.title.ilike(pattern), Movie.overview.ilike(pattern))).limit(limit)
    )
    return {"items": [movie_to_schema(m) for m in result.scalars().all()]}


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> MovieOut:
    movie = await db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie_to_schema(movie)
