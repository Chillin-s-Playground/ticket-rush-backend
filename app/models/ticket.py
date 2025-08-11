from sqlalchemy import Column, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, SMALLINT

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="유저 id",
    )


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = UniqueConstraint(
        "row_label", "seat_no", name="uq_seat"
    )  # A10 같은 row_label과 seat_no의 조합은 딱 한 번만 가능

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
        UniqueConstraint("seat_id", name="uq_sold_once"),  # 좌석은 1번만 판매
        UniqueConstraint("user_id", name="uq_user_one"),  # 유저는 전체에서 1좌석만
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
    user_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        comment="유저 FK",
    )
    purchased_at = Column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.now(),
        comment="구매 시각",
    )
