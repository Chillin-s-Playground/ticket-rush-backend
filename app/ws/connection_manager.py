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

    async def broadcast(self, room_id: str, message: dict):
        async with self._lock:
            conns = list(self.rooms.get(room_id, ()))

        dead: List[WebSocket] = []

        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                room = self.rooms.get(room_id)
                if room:
                    for w in dead:
                        room.discard(w)
                    if not room:
                        self.rooms.pop(room_id, None)
