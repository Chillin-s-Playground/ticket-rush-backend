from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.mysql import get_session_dependency
from app.core.redis import get_redis

api_router = APIRouter(prefix="/health", tags=["health"])


@api_router.get("/health/db")
def health_db(db: Session = Depends(get_session_dependency)):
    """DB 연결·세션 의존성 헬스체크."""

    db.execute(text("SELECT 1"))
    return {"ping": True}


@api_router.get("/health/redis")
async def health_redis(r=Depends(get_redis)):
    """redis 연결 헬스체크."""

    await r.set("ping", "pong")
    ping = await r.get("ping")
    return {"ping": ping}
