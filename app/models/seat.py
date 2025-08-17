from sqlalchemy import Column, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, SMALLINT

from app.models.base import Base


class Seat(Base):
    __tablename__ = "seats"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="좌석 id",
    )
    row_label = Column(String(10), nullable=False, comment="행 라벨 (예: A, B, A)")
    seat_no = Column(
        SMALLINT(unsigned=True), nullable=False, comment="좌석 번호 (1..N)"
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("user_uuid", name="uq_user_one"),  # 유저는 전체에서 1좌석만
    )

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="티켓 id",
    )
    seat_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("seats.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        comment="좌석 FK",
    )
    user_uuid = Column(String(36), nullable=False)
    purchased_at = Column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
        comment="구매 시각",
    )
