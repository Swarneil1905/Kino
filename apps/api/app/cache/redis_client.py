from redis.asyncio import Redis

from app.core.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_cache(key: str) -> str | None:
    try:
        return await redis.get(key)
    except Exception:
        return None


async def set_cache(key: str, value: str, ttl: int = 900) -> None:
    try:
        await redis.set(key, value, ex=ttl)
    except Exception:
        pass


async def delete_cache(key: str) -> None:
    try:
        await redis.delete(key)
    except Exception:
        pass
