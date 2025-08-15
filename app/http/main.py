from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exception import UnknownException, exception_handler
from app.http.health import router as health
from app.http.ticket import router as ticket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health)
app.include_router(ticket)

app.add_exception_handler(UnknownException, exception_handler)
