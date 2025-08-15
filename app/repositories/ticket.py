from typing import Optional
from uuid import uuid4

import redis
from sqlalchemy.orm import Session


class TicketRepository:
    def __init__(
        self, db: Optional[Session] = None, redis: Optional[redis.Redis] = None
    ) -> None:
        self.db = db
        self.redis = redis

    async def check_and_join_queue(self, event_id: int, user_uuid: str, expire: int):
        """중복체크 후 대기열 입장."""

        waiting_key = f"queue:waiting:{event_id}"  # 대기열 key
        joined_key = f"queue:joined:{event_id}:{user_uuid}"  # 대기열에 중복유저 못들어가게 막는 key

        # join 안된 유저는 ok 변수에 반환값 할당
        ok = await self.redis.set(joined_key, "1", ex=expire, nx=True)
        if ok:
            # waiting list에 넣기
            await self.redis.rpush(waiting_key, user_uuid)

    async def admit_token_to_waiting_user(
        self, event_id: int, user_uuid: str, expire: int, limit: int = 700
    ):
        """입장가능한 유저에게 token 발행."""

        active_user_key = f"active:{event_id}"
        active_user_count = await self.redis.scard(active_user_key)

        # 활성유저 (사이트에 접속한 유저)
        if active_user_count <= limit and not await self.redis.sismember(
            active_user_key, user_uuid
        ):
            waiting_key = f"queue:waiting:{event_id}"
            joined_key = f"queue:joined:{event_id}:{user_uuid}"

            token = f"{event_id}:{uuid4()}"
            token_key = f"gate:token:{token}"
            await self.redis.set(token_key, user_uuid, ex=expire, nx=True)
            await self.redis.sadd(active_user_key, user_uuid)  # 활성유저에 추가
            await self.redis.lpop(waiting_key)
            await self.redis.delete(joined_key)

            return {"token": token}
