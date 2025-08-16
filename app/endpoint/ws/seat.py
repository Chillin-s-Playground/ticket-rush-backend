import json

from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.connection_manager import ConnectManager, get_manager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_router = APIRouter()


@ws_router.websocket("/ws/events/{event_id}/seats")
async def seat_ws(
    ws: WebSocket, event_id: int, manager: ConnectManager = Depends(get_manager)
):
    """좌석 상태 실시간 업데이트를 위한 연결 장치"""

    room_id = f"event:{event_id}:seat_update"
    await manager.connect(ws, room_id)
    try:
        while True:
            message = await ws.receive_text()
            print(f"{room_id}에서 온 메세지 : ", message)
    except WebSocketDisconnect:
        print(f"Client disconnected from room: {room_id}")
    except Exception as e:
        print(f"WebSocket error in room {room_id}: {e}")
    finally:
        await manager.disconnect(ws, room_id)
