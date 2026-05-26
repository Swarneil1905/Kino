"""Add Google OAuth and admin columns to users.

Revision ID: 002
Revises: 001
Create Date: 2026-05-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", nullable=True)
    op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("auth_provider", sa.String(20), nullable=False, server_default="email"))
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "google_id")
    op.alter_column("users", "password_hash", nullable=False)
