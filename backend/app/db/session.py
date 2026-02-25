from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def _build_session_factory(database_url: str):
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session_factory = _build_session_factory(get_settings().database_url)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
