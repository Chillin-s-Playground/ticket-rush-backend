from fastapi import FastAPI

from app.http.health import router as health
from app.http.ticket import router as ticket

app = FastAPI()

app.include_router(health)
app.include_router(ticket)
