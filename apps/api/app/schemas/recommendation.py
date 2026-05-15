from datetime import datetime

from pydantic import BaseModel

from app.schemas.movie import MovieOut


class RecommendationResponse(BaseModel):
    movies: list[MovieOut]
    cache_hit: bool
    computed_at: datetime
