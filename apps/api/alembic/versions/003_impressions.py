"""add impressions table

Revision ID: 003_impressions
Revises: 002_google_oauth_admin
Create Date: 2026-05-30
"""
from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_impressions"
down_revision = "002_google_oauth_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "impressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("movie_id", sa.Integer, sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False, server_default="v1-baseline"),
        sa.Column("shown_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("clicked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_impressions_user_id", "impressions", ["user_id"])
    op.create_index("ix_impressions_movie_id", "impressions", ["movie_id"])
    op.create_index("ix_impressions_shown_at", "impressions", ["shown_at"])
    op.create_index("ix_impressions_model_version", "impressions", ["model_version"])


def downgrade() -> None:
    op.drop_table("impressions")
