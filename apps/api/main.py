import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

from app.core.config import settings
from app.core.lifespan import lifespan
from app.routers import admin, auth, metrics, movies, ratings, recommendations

app = FastAPI(title="Kino API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "model_loaded": getattr(app.state, "model_loaded", False)}


app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
app.include_router(metrics.router)
app.include_router(admin.router)
