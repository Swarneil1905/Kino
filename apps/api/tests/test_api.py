import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    import uuid
    email = f"test-{uuid.uuid4().hex[:8]}@kino.dev"
    reg = await client.post("/auth/register", json={"email": email, "password": "secretpass123"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    assert reg.json()["user_id"]

    login = await client.post("/auth/login", json={"email": email, "password": "secretpass123"})
    assert login.status_code == 200
    assert login.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_movies_list(client: AsyncClient):
    response = await client.get("/movies?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "recall_at_10" in response.json()
