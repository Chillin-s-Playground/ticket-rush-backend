import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.utils.parser import build_seat_update_payload
from app.ws.connection_manager import ConnectManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    room_id = None

    try:
        # 1. 처음 Connection
        raw_connection = await ws.receive_text()
        msg = json.loads(raw_connection)
        ws_type, ws_payload = msg.get("type"), msg.get("payload", {})

        if not msg or ws_type != "join_seat":
            await ws.send_json({"type": "error", "payload": {"code": "JOIN_FIRST"}})
            await ws.close()
            return

        # 2. Room 입장
        room_id = str(ws_payload.get("room_id", None))
        if not room_id:
            await ws.send_json(
                {
                    "type": "error",
                    "payload": {"code": "INVALID_PAYLOAD", "field": "room_id"},
                }
            )
            await ws.close()
            return

        await manager.join(room_id=room_id, ws=ws)
        await ws.send_text(f"룸에 등장 : {room_id}")

        # 3. 라우팅 루프: seat_hold / seat_sold / seat_available만 처리
        while True:
            raw_msg = await ws.receive_text()
            msg = json.loads(raw_msg)
            event_id, seat_label = msg.get("event_id"), msg.get("seat_label")

            payload = build_seat_update_payload(
                type=ws_type, event_id=event_id, seat_label=seat_label
            )
            if not payload:
                continue

            await manager.broadcast(
                room_id=room_id, message={"type": "seat_update", "payload": payload}
            )
    except WebSocketDisconnect:
        if room_id:
            await manager.leave(room_id=room_id, ws=ws)
