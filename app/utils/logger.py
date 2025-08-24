import contextvars
import logging

logger = logging.getLogger("seat")

request_id_ctx = contextvars.ContextVar("request_id", default="-")


def log_seat_action(seat_id, user_id, redis_result):
    rid = request_id_ctx.get()
    logger.info(
        f"[request_id={rid}] seat_id={seat_id} user_id={user_id} redis_result={redis_result}"
    )
