import json

from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.connection_manager import ConnectManager, get_manager
from app.utils.parser import build_seat_update_payload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# manager = ConnectManager()


# @app.websocket("/ws")
# async def websocket_endpoint(ws: WebSocket):
#     """접속 테스트 용."""
#     await ws.accept()
#     room_id = None

#     try:
#         # 1. 처음 Connection
#         raw_connection = await ws.receive_text()
#         msg = json.loads(raw_connection)
#         ws_type, ws_payload = msg.get("type"), msg.get("payload", {})

#         if not msg or ws_type != "join_seat":
#             await ws.send_json({"type": "error", "payload": {"code": "JOIN_FIRST"}})
#             await ws.close()
#             return

#         # 2. Room 입장
#         room_id = str(ws_payload.get("room_id", None))
#         if not room_id:
#             await ws.send_json(
#                 {
#                     "type": "error",
#                     "payload": {"code": "INVALID_PAYLOAD", "field": "room_id"},
#                 }
#             )
#             await ws.close()
#             return

#         await manager.join(room_id=room_id, ws=ws)
#         await ws.send_text(f"룸에 등장 : {room_id}")

#         # 3. 라우팅 루프: seat_hold / seat_sold / seat_available만 처리
#         while True:
#             raw_msg = await ws.receive_text()
#             msg = json.loads(raw_msg)
#             event_id, seat_label = msg.get("event_id"), msg.get("seat_label")

#             payload = build_seat_update_payload(
#                 type=ws_type, event_id=event_id, seat_label=seat_label
#             )
#             if not payload:
#                 continue

#             await manager.broadcast(
#                 room_id=room_id, message={"type": "seat_update", "payload": payload}
#             )
#     except WebSocketDisconnect:
#         if room_id:
#             await manager.leave(room_id=room_id, ws=ws)


ws_router = APIRouter()


@ws_router.websocket("/ws/events/{event_id}/seats")
async def seat_ws(
    ws: WebSocket, event_id: int, manager: ConnectManager = Depends(get_manager)
):
    """좌석 상태 실시간 업데이트를 위한 연결 장치"""

    room_id = f"event:{event_id}:seat_update"
    await manager.connect(ws, room_id)
    try:
        # 클라이언트로부터 메시지를 계속 기다립니다.
        # 클라이언트가 메시지를 보내지 않더라도 연결을 유지하려면 이 루프가 필요합니다.
        while True:
            # 클라이언트가 메시지를 보내지 않더라도 receive_text()는 블로킹됩니다.
            # 연결이 끊어지거나 서버가 닫힐 때까지 대기합니다.
            # 필요하다면 await websocket.receive_json() 등으로 변경 가능
            message = await ws.receive_text()
            # 여기에 클라이언트로부터 받은 메시지 처리 로직을 추가할 수 있습니다.
            print(f"Received from client in room {room_id}: {message}")
    except WebSocketDisconnect:
        print(f"Client disconnected from room: {room_id}")
    except Exception as e:
        print(f"WebSocket error in room {room_id}: {e}")
    finally:
        # 예외 발생 시 또는 연결 종료 시, manager에서 웹소켓을 제거합니다.
        # 이 `disconnect` 호출 내부에 `await ws.close()`가 있다면 해당 문제와 연관될 수 있습니다.
        # manager.disconnect 내부에서 Starlette의 ws.close()를 직접 호출하는 대신
        # Starlette가 연결 종료를 처리하도록 맡기는 것이 더 안전할 수 있습니다.
        await manager.disconnect(ws, room_id)
