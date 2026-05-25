import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture(scope="session")
async def client():
    """Single AsyncClient shared across the whole test session.

    Using scope='session' combined with asyncio_mode=auto and a session-scoped
    event loop means all tests share one loop and one DB connection pool --
    no 'Future attached to a different loop' errors.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
