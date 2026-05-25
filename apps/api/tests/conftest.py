import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture(scope="session")
async def client():
    """Single AsyncClient shared across the whole test session.

    scope='session' + asyncio_default_fixture_loop_scope=session means one
    event loop for all tests, so the DB connection pool is never attached to
    a closed loop.

    Entering the lifespan context triggers init_database() which creates all
    tables via SQLAlchemy metadata.create_all before any test runs.
    """
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
