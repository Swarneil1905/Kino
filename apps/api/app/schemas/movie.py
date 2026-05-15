from pydantic import BaseModel

from app.models.movie import Movie


class MovieOut(BaseModel):
    id: int
    title: str
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    release_year: int | None = None
    genres: list[str] = []
    match_percent: int = 80
    duration: str = "2h 00m"
    maturity_rating: str = "PG-13"
    vote_average: float = 0.0


class MovieListOut(BaseModel):
    items: list[MovieOut]
    total: int
    page: int


def _format_duration(minutes: int | None) -> str:
    if not minutes:
        return "2h 00m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m" if hours else f"{mins}m"


def movie_to_schema(movie: Movie, match_percent: int = 85) -> MovieOut:
    return MovieOut(
        id=movie.id,
        title=movie.title,
        overview=movie.overview or "",
        poster_path=movie.poster_path,
        backdrop_path=movie.backdrop_path,
        release_year=movie.release_year,
        genres=list(movie.genres or []),
        match_percent=match_percent,
        duration=_format_duration(movie.runtime_minutes),
        maturity_rating=movie.maturity_rating or "PG-13",
        vote_average=float(movie.vote_average or 0.0),
    )
