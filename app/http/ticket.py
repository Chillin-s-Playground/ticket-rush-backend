import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.mysql import get_session_dependency
from app.core.redis import get_redis
from app.core.token import verify_token
from app.schema.ticket import HoldSeatRequestDTO, JoinRequestDTO
from app.services.ticket import TicketService

router = APIRouter()


@router.post("/seats")
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


@router.post("/queue/join/{event_id}")
async def queue_and_join(
    req: JoinRequestDTO, event_id: int = 123, redis: redis.Redis = Depends(get_redis)
):
    """사이트 진입 시, 5분 제한 토큰 발행 API"""
    return await TicketService(redis=redis).queue_and_join(
        event_id=event_id, user_uuid=req.user_uuid
    )
