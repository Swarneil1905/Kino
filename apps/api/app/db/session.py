import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool in test mode: each request gets a fresh connection with no
# cross-loop binding, eliminating "Future attached to a different loop" errors.
_test_mode = os.getenv("TEST_MODE") == "1"
engine = create_async_engine(
    settings.database_url,
    **({} if _test_mode else {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}),
    **({"poolclass": NullPool} if _test_mode else {}),
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
