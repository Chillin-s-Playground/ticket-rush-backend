from pydantic import BaseModel, Field


class JoinRequestDTO(BaseModel):
    user_uuid: str


class SeatModel(BaseModel):
    seat_id: int = Field(..., description="Seats 테이블의 id")
    seat_label: str = Field(..., description="좌석번호", examples=["A1"])
    status: str = Field(default="AVAILABLE", description="상태")
