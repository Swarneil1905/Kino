from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.db.base import Base


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(item_type=float), nullable=False)
    computed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
