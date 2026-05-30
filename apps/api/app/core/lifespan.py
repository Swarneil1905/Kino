from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.init_db import init_database
from app.db.session import AsyncSessionLocal
from app.ml.inference import RecommendationEngine
from app.scripts.seed_demo_accounts import seed_demo_accounts
from app.scripts.seed_movies import seed_movies


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_database()

    async with AsyncSessionLocal() as session:
        await seed_movies(session, max_movies=3000)
        await seed_demo_accounts(session)

    engine = RecommendationEngine()
    engine.load()
    app.state.recommendation_engine = engine
    app.state.model_loaded = engine.loaded
    yield
