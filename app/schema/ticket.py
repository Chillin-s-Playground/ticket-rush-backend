from typing import List, Optional

from pydantic import BaseModel, Field


class JoinRequestDTO(BaseModel):
    user_uuid: str


class SeatModel(BaseModel):
    seat_id: int = Field(..., description="Seats 테이블의 id")
    seat_label: str = Field(..., description="좌석번호", examples=["A1"])
    status: str = Field(default="AVAILABLE", description="상태")


class GetSeatResponseDTO(BaseModel):
    seat_list: List[SeatModel] = Field(..., description="좌석 리스트")
    my_paid_label: Optional[str] = Field(
        default=None, description="결제한 좌석이 있다면, 내려준다."
    )


class HoldSeatRequestDTO(BaseModel):
    seat_id: int = Field(..., description="Seats 테이블의 id")
    seat_label: str = Field(..., description="좌석번호", examples=["A1"])
    status: str = Field(default="AVAILABLE", description="상태")
    prev_seat_id: Optional[int] = Field(
        default=None, description="기존 Seats 테이블의 id"
    )
    prev_seat_label: Optional[str] = Field(
        default=None, description="기존 좌석번호", examples=["A1"]
    )


class PaySeatRequestDTO(BaseModel):
    seat_id: Optional[int] = Field(default=None, description="Seats 테이블의 id")
    seat_label: Optional[str] = Field(
        default=None, description="좌석번호", examples=["A1"]
    )
