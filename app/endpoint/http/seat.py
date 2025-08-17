import redis
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.connection_manager import ConnectManager, get_manager
from app.core.mysql import get_session_dependency
from app.core.redis import get_redis
from app.core.token import verify_token
from app.models.seat import Seat
from app.schema.seat import (
    DeactivateRequestDTO,
    HoldSeatRequestDTO,
    JoinRequestDTO,
    PaySeatRequestDTO,
)
from app.services.seat import TicketService

api_router = APIRouter()


@api_router.post("/seats")
async def insert_seed_seats(db: Session = Depends(get_session_dependency)):
    """시드 좌석 적재"""

    seed_seats: list[dict] = []

    TOTAL = 3200  # 총 좌석 수
    PER_ROW = 80  # 행당 좌석 수
    seat_label_no = -1

    for idx in range(TOTAL):
        seat_no = (idx % PER_ROW) + 1

        if idx % 80 == 0:
            seat_label_no += 1

        if seat_label_no < 26:
            row_label = chr(65 + seat_label_no)
        else:
            row_label = f"A{chr(65 + seat_label_no -26)}"

        seed_seats.append(dict(row_label=row_label, seat_no=seat_no))

    try:
        db.bulk_insert_mappings(Seat, seed_seats)
        db.commit()
    except Exception as e:
        print(str(e))


@api_router.post("/queue/join/{event_id}")
async def queue_and_join(
    req: JoinRequestDTO, event_id: int = 123, redis: redis.Redis = Depends(get_redis)
):
    """사이트 진입 시, 5분 제한 토큰 발행 API"""
    return await TicketService(redis=redis).queue_and_join(
        event_id=event_id, user_uuid=req.user_uuid
    )


@api_router.get("/events/{event_id}/seats")
async def get_seat_states(
    event_id: int,
    user_uuid: str = Depends(verify_token),
    db: Session = Depends(get_session_dependency),
    redis: redis.Redis = Depends(get_redis),
):
    """처음 좌석상태 조회하는 API."""
    return await TicketService(db=db, redis=redis).get_seats(
        event_id=event_id, user_uuid=user_uuid
    )


@api_router.post("/events/{event_id}/seats/hold")
async def hold_the_seat(
    event_id: int,
    req: HoldSeatRequestDTO,
    user_uuid=Depends(verify_token),
    redis: redis.Redis = Depends(get_redis),
    manager: ConnectManager = Depends(get_manager),
):
    """좌석 HOLD 처리"""

    return await TicketService(redis=redis, manager=manager).hold_the_seat(
        user_uuid=user_uuid,
        event_id=event_id,
        seat_id=req.seat_id,
        seat_label=req.seat_label,
        seat_status=req.status,
        prev_seat_id=req.prev_seat_id,
        prev_seat_label=req.prev_seat_label,
    )


@api_router.post("/events/{event_id}/seats/pay")
async def hold_the_seat(
    event_id: int,
    req: PaySeatRequestDTO,
    user_uuid=Depends(verify_token),
    db: Session = Depends(get_session_dependency),
    redis: redis.Redis = Depends(get_redis),
    manager: ConnectManager = Depends(get_manager),
):
    """좌석 SOLD 처리"""

    return await TicketService(db=db, redis=redis, manager=manager).sold_the_seat(
        event_id=event_id,
        seat_id=req.seat_id,
        seat_label=req.seat_label,
        user_uuid=user_uuid,
    )


@api_router.post("/events/{event_id}/presence/leave")
async def leave(
    req: DeactivateRequestDTO,
    event_id: int,
    user_uuid: str = Depends(verify_token),
    redis: redis.Redis = Depends(get_redis),
    background_tasks: BackgroundTasks = None,
):
    service = TicketService(redis=redis)
    background_tasks.add_task(service.cleanup_user, event_id, user_uuid, req.seat_label)
    return {"ok": True}
