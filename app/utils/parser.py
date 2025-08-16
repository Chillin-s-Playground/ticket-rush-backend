def build_seat_update_payload(type: str, event_id: int, seat_label: str) -> dict | None:
    """좌석상태 업데이트용 payload 반환 메소드."""

    if type == "seat_hold":
        return {
            "event_id": event_id,
            "seat_label": seat_label,
            "seat_status": "HOLD",
        }
    elif type == "seat_sold":
        return {
            "event_id": event_id,
            "seat_label": seat_label,
            "seat_status": "SOLD",
        }
    elif type == "seat_available":
        return {
            "event_id": event_id,
            "seat_label": seat_label,
            "seat_status": "AVAILABLE",
        }
    else:
        return None


def build_payload(*seats: tuple[int, str], with_prev=False):
    """좌석 상태 변경 payload 생성"""
    payload = []
    for seat in seats:
        seat_id, seat_status = seat
        key = "seat_id" if not with_prev else "prev_seat_id"
        payload.append(
            {
                key if seat == seats[-1] and with_prev else "seat_id": seat_id,
                f"{'prev_' if with_prev and seat == seats[-1] else ''}seat_status": seat_status,
            }
        )
    return payload
