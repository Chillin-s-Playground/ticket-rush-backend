from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_dependency
from app.models.ticket import Seat

app = FastAPI()


@app.get("/health/db")
def health_db(db: Session = Depends(get_session_dependency)):
    """DDB 연결·세션 의존성 헬스체크."""

    db.execute(text("SELECT 1"))
    return {"ping": True}


@app.post("/seats")
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
