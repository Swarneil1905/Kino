from datetime import datetime

from pydantic import BaseModel, Field


class RatingIn(BaseModel):
    movie_id: int
    value: int | None = Field(default=None, description="1, -1, or null to remove")


class RatingOut(BaseModel):
    movie_id: int
    value: int | None
    updated_at: datetime


class RatingsListOut(BaseModel):
    ratings: list[RatingOut]
