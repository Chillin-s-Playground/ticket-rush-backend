import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
        first = await ws.receive_text()
        msg = json.loads(first)
        if msg.get("type") != "join_seat":
            await ws.send_text("join_seat 방 외에는 없음.")
            await ws.close()
            raise WebSocketDisconnect()

        # 룸 입장
        room_id = str(msg["payload"]["room_id"])
        await manager.join(room_id=room_id, ws=ws)
        await ws.send_text(f"룸에 등장 : {room_id}")

        # 메세지 에코
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"{room_id} : {data}")

    except WebSocketDisconnect:
        if room_id:
            await manager.leave(room_id=room_id, ws=ws)
