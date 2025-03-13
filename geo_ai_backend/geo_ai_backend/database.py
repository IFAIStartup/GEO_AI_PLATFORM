from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, session, sessionmaker

from geo_ai_backend.config import settings


DATABASE_URL = settings.DATABASE_URL
POOL_SIZE_ENGINE = settings.POOL_SIZE_ENGINE
engine = create_engine(DATABASE_URL, pool_size=POOL_SIZE_ENGINE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> session.Session:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_db_iter() -> session.Session:
    return next(get_db())
