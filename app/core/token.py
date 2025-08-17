# 약간 뭐라해야하지 비로그인 방식이라 auth는 아니고, token이 좀 더 맞는 명칭 같아서 token.py 파일이라고 명명함.
import redis
from fastapi import Depends, HTTPException

from app.core.redis import get_redis


async def verify_token(
    token: str, redis: redis.Redis = Depends(get_redis)
) -> str | None:
    """토큰 유효성 검사"""

    vaild_token = await redis.get(f"gate:token:{token}")

    if not vaild_token:
        raise HTTPException(
            status_code=401, detail="유효하지 않은 세션입니다. 다시 시도해주세요."
        )

    return vaild_token
