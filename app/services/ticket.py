from typing import Optional

import redis
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.connection_manager import ConnectManager
from app.core.exception import UnknownException
from app.models.ticket import Seat
from app.repositories.ticket import TicketRepository
from app.utils.parser import build_payload

JOIN_EXPIRE = 5 * 60
TOKEN_EXPIRE = 30 * 60
HOLD_EXPIRE = 2 * 60


manager = ConnectManager()


class TicketService:
    def __init__(
        self,
        db: Optional[Session] = None,
        redis: Optional[redis.Redis] = None,
        manager: Optional[ConnectManager] = None,
    ) -> None:
        self.db = db
        self.redis = redis
        self.manager = manager

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

    async def get_seats(self, event_id: int):
        try:
            ticket_repo = TicketRepository(db=self.db, redis=self.redis)

            # 2. SOLD 상태 포함 좌석 조회
            seat_list = await ticket_repo.get_sold_seat_list()

            # 3. HOLD 좌석 ID set (Redis)
            hold_values = await ticket_repo.get_hold_set(
                event_id=event_id, seat_list=seat_list
            )

            # 4. 좌석리스트 상태 조합
            if hold_values:
                hold_set = {
                    seat_list[i].seat_id for i, v in enumerate(hold_values) if v
                }

                for s in seat_list:
                    if s.status != "SOLD" and s.seat_id in hold_set:
                        s.status = "HOLD"

            return seat_list

        except Exception as e:
            raise e

    async def hold_the_seat(
        self,
        user_uuid: str,
        event_id: int,
        seat_id: int,
        seat_label: str,
        seat_status: str,
        prev_seat_id: Optional[int] = None,
        prev_seat_label: Optional[str] = None,
    ):
        try:
            ticket_repo = TicketRepository(redis=self.redis)

            # 1. 좌석상태 분기처리
            if not prev_seat_label:  # 처음 좌석 선택
                locked = await ticket_repo.hold_the_seat(
                    event_id=event_id,
                    seat_label=seat_label,
                    user_uuid=user_uuid,
                    expire=HOLD_EXPIRE,
                )
                if not locked:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="이미 선택된 좌석입니다.",
                    )
                payload = build_payload((seat_id, "HOLD"))

            elif (
                prev_seat_label == seat_label and seat_status == "HOLD"
            ):  # 선택한 좌석 취소
                await ticket_repo.del_hold_the_seat(
                    event_id=event_id, seat_label=seat_label
                )
                payload = build_payload((seat_id, "AVAILABLE"))

            else:  # 좌석 변경
                locked = await ticket_repo.hold_the_seat(
                    event_id=event_id,
                    seat_label=seat_label,
                    user_uuid=user_uuid,
                    expire=HOLD_EXPIRE,
                )
                if not locked:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="이미 선택된 좌석입니다.",
                    )
                await ticket_repo.del_hold_the_seat(
                    event_id=event_id, seat_label=prev_seat_label
                )

                payload = [
                    {"seat_id": seat_id, "seat_status": "HOLD"},
                    {"seat_id": prev_seat_id, "seat_status": "AVAILABLE"},
                ]

            # 2. 변경된 사항 브로드캐스트.
            await self.manager.broadcast(
                room_id=f"event:{event_id}:seat_update",
                message={"type": "seat_update", "payload": payload},
            )

            return {
                "seat_id": seat_id,
                "seat_label": seat_label,
                "seat_status": "AVAILABALE" if seat_status == "HOLD" else "HOLD",
            }

        except Exception as e:
            raise e

    async def sold_the_seat(
        self,
        event_id: int,
        user_uuid: str,
        seat_id: Optional[int] = None,
        seat_label: Optional[str] = None,
    ):
        """좌석 결제완료 처리 하는 서비스 로직."""
        try:
            ticket_repo = TicketRepository(db=self.db, redis=self.redis)

            if not seat_id or not seat_label:
                print("seat_id 없어서 발생하는 에러")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="좌석을 선택한 후 결제를 진행해주세요.",
                )

            # 1. SOLD된 좌석인지 체크하는 로직
            is_sold = await ticket_repo.is_exist_sold_seat(
                seat_id=seat_id,
            )

            if is_sold:
                print("이미 결제가 완료된 좌석")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 결제가 완료된 좌석입니다.",
                )

            # 2. HOLD하고 있는 좌석 있는지 체크
            is_hold = await ticket_repo.is_exist_hold_seat(
                event_id=event_id,
                seat_label=seat_label,
            )

            if not is_hold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="좌석을 선택한 후 결제를 진행해주세요.",
                )

            if is_hold != user_uuid:
                print("해당 유저가 선택한 좌석이 아님")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 다른 사용자가 선택한 좌석입니다.",
                )

            # 3. 결제 처리
            await ticket_repo.set_sold_seat(user_uuid=user_uuid, seat_id=seat_id)
            await ticket_repo.del_hold_the_seat(
                event_id=event_id, seat_label=seat_label
            )

            # 4. broadcast
            await self.manager.broadcast(
                room_id=f"event:{event_id}:seat_update",
                message={
                    "type": "seat_update",
                    "payload": {"seat_id": seat_id, "seat_status": "SOLD"},
                },
            )

            return {"message": "결제완료"}

        except Exception as e:
            raise e
