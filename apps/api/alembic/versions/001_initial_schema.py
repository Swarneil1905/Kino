"""Initial schema: users, movies, ratings, interactions, user_embeddings.

Revision ID: 001
Revises:
Create Date: 2026-05-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tmdb_id", sa.Integer(), unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("overview", sa.Text(), server_default=""),
        sa.Column("poster_path", sa.String(255)),
        sa.Column("backdrop_path", sa.String(255)),
        sa.Column("release_year", sa.SmallInteger()),
        sa.Column("runtime_minutes", sa.SmallInteger()),
        sa.Column("maturity_rating", sa.String(10)),
        sa.Column("vote_average", sa.Numeric(3, 1)),
        sa.Column("genres", postgresql.ARRAY(sa.String(50)), nullable=False, server_default="{}"),
        sa.Column("popularity_score", sa.Numeric(10, 4)),
    )
    op.create_table(
        "ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_rating_user_movie"),
    )
    op.create_index("ix_ratings_user_created", "ratings", ["user_id", "created_at"])
    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_interactions_user_created", "interactions", ["user_id", "created_at"])
    op.create_table(
        "user_embeddings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("user_embeddings")
    op.drop_index("ix_interactions_user_created", table_name="interactions")
    op.drop_table("interactions")
    op.drop_index("ix_ratings_user_created", table_name="ratings")
    op.drop_table("ratings")
    op.drop_table("movies")
    op.drop_table("users")
