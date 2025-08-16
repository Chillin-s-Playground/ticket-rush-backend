import asyncio
from typing import Dict, List, Set

from fastapi import WebSocket


class ConnectManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = (
            {}
        )  # ticket:1 : {브라우저 A, 브라우저 B, ...}
        self._lock = asyncio.Lock()

    async def join(self, room_id: str, ws: WebSocket):
        async with self._lock:
            self.rooms.setdefault(room_id, set()).add(ws)

    async def leave(self, room_id: str, ws: WebSocket):
        async with self._lock:
            conns = self.rooms.get(room_id)

            if not conns:  # 방이 없거나 이미 비어 있음
                self.rooms.pop(room_id, None)
                return

            conns.discard(ws)

            if not conns:  # 내가 마지막 사람이었을 경우
                self.rooms.pop(room_id, None)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        async with self._lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = set()
            self.rooms[room_id].add(websocket)
            print(
                f"✅ WebSocket connected to room: {room_id}, total connections: {len(self.rooms[room_id])}"
            )

    async def disconnect(self, websocket: WebSocket, room_id: str):
        async with self._lock:
            if room_id in self.rooms:
                self.rooms[room_id].discard(websocket)
                print(
                    f"❌ WebSocket disconnected from room: {room_id}, remaining: {len(self.rooms[room_id])}"
                )
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
                else:
                    print(
                        f"Room {room_id} still has {len(self.rooms[room_id])} connections."
                    )

    async def broadcast(self, room_id: str, message: dict):
        async with self._lock:
            conns = list(self.rooms.get(room_id, ()))
            print(
                f"Attempting to broadcast to room: {room_id} with {len(conns)} connections."
            )

        dead: List[WebSocket] = []
        for ws in conns:
            try:
                print("message ---> ", message)
                await ws.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to a WebSocket: {e}")
                dead.append(ws)

        if dead:
            async with self._lock:
                room = self.rooms.get(room_id)
                if room:
                    for w in dead:
                        room.discard(w)
                    if not room:
                        self.rooms.pop(room_id, None)


app_manager = ConnectManager()


def get_manager():
    return app_manager
