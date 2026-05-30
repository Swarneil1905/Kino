from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import engine
from app.models.interaction import Interaction  # noqa: F401
from app.models.movie import Movie  # noqa: F401
from app.models.rating import Rating  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_embedding import UserEmbedding  # noqa: F401
from app.models.impression import Impression  # noqa: F401


async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
