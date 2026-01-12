from __future__ import annotations

import os
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


def normalize_database_url(url: str) -> str:
    """
    Ensure SQLAlchemy uses psycopg v3 instead of defaulting to psycopg2.

    - postgres://...      -> postgresql+psycopg://...
    - postgresql://...    -> postgresql+psycopg://...
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url.split("://", 1)[0]:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Add it in your environment variables.")
    return normalize_database_url(url)


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


Base = declarative_base()


def _get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = _get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
