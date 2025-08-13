from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Configs

config = Configs()

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    """요청 단위 세션 의존성"""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_session_dependency():
    """컨텍스트 매니저로 세션을 열고 닫기만 하는 의존성"""
    with Session(engine) as session:
        yield session
