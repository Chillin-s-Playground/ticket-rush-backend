import asyncio
from typing import Dict, Set

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


manager = ConnectManager()
