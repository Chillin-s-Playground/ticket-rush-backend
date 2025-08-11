from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session_dependency

app = FastAPI()


@app.get("/health/db")
def health_db(db: Session = Depends(get_session_dependency)):
    """DDB 연결·세션 의존성 헬스체크."""

    db.execute(text("SELECT 1"))
    return {"ping": True}
