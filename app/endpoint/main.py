from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exception import UnknownException, exception_handler
from app.endpoint.http.health import api_router as health
from app.endpoint.http.seat import api_router as seat
from app.endpoint.ws.seat import ws_router as seat_ws

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health)
app.include_router(seat)
app.include_router(seat_ws)

app.add_exception_handler(UnknownException, exception_handler)
