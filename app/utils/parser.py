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
