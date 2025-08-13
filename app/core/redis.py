import redis.asyncio as redis

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:

    global _redis
    if _redis is None:
        _redis = redis.from_url(
            "redis://localhost:6379/0",
            decode_responses=True,
        )
    return _redis
