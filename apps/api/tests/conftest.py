import os

# Must be set before any app module is imported so session.py picks up NullPool.
# NullPool gives each request a fresh connection with no event-loop binding,
# which eliminates "Future attached to a different loop" errors in async tests.
os.environ.setdefault("TEST_MODE", "1")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(scope="session")
async def client():
    """Single AsyncClient for the whole session — one event loop, NullPool DB."""
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
