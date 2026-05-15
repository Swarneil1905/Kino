from sqlalchemy import Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    overview: Mapped[str] = mapped_column(Text, default="")
    poster_path: Mapped[str | None] = mapped_column(String(255))
    backdrop_path: Mapped[str | None] = mapped_column(String(255))
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    runtime_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    maturity_rating: Mapped[str | None] = mapped_column(String(10))
    vote_average: Mapped[float | None] = mapped_column(Numeric(3, 1))
    genres: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)
    popularity_score: Mapped[float | None] = mapped_column(Numeric(10, 4))
