from typing import Optional
from uuid import uuid4

import redis
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exception import UnknownException
from app.repositories.ticket import TicketRepository
from app.ws.connection_manager import ConnectManager

JOIN_EXPIRE = 5 * 60
TOKEN_EXPIRE = 5 * 60
HOLD_EXPIRE = 2 * 60


manager = ConnectManager()


class TicketService:
    def __init__(
        self, db: Optional[Session] = None, redis: Optional[redis.Redis] = None
    ) -> None:
        self.db = db
        self.redis = redis

    async def queue_and_join(self, event_id: int, user_uuid: str):
        """대기열 입장 및 토큰 발행하는 서비스 로직."""
        try:
            ticket_repo = TicketRepository(redis=self.redis)

            # 1. 중복체크 후 대기열 입장
            await ticket_repo.check_and_join_queue(
                event_id=event_id, user_uuid=user_uuid, expire=JOIN_EXPIRE
            )

            # 2. 대기열에 있는 유저에게 토큰 발행
            token = await ticket_repo.admit_token_to_waiting_user(
                event_id=event_id, user_uuid=user_uuid, expire=TOKEN_EXPIRE
            )

            if not token:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="현재 대기 인원이 많으니 잠시만 기다려주세요",
                )

            return token

        except Exception as e:
            raise UnknownException(str(e))
