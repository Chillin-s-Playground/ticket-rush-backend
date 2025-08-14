from typing import Optional
from uuid import uuid4

import redis
from sqlalchemy.orm import Session

EXPIRE = 5 * 60


class TicketService:
    def __init__(
        self, db: Optional[Session] = None, redis: Optional[redis.Redis] = None
    ) -> None:
        self.db = db
        self.redis = redis

    async def queue_and_join(self, event_id: int, user_uuid: str):
        """대기열 입장 및 토큰 발행하는 서비스 로직."""
        try:
            # 1. 대기열 입장
            await self.redis.rpush(f"queue:waiting:{event_id}", user_uuid)

            # 2. 활성유저 (토큰받아서 사이트 진입한 유저)가 500명 이하일 때, 대기열에 있는 유저 순서대로 토큰발행 후 set
            active_count = len(await self.redis.keys("gate:token:*"))
            if active_count <= 500:
                token = f"{event_id}:{uuid4()}"
                token_key = f"gate:token:{token}"
                await self.redis.set(token_key, user_uuid, ex=EXPIRE, nx=True)

                # 3. 대기열에서 유저 제거
                await self.redis.lpop(f"queue:waiting:{event_id}")
            return token
        except Exception as e:
            raise e
