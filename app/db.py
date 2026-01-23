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
    
    Also ensures sslmode=require for Neon compatibility.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Add it in your environment variables.")
    return normalize_database_url(url)


@lru_cache
def get_engine() -> Engine:
    """
    Create SQLAlchemy engine optimized for serverless (Vercel + Neon).
    
    - pool_pre_ping: Verify connections before use (handles serverless cold starts)
    - pool_size=5: Small pool for serverless
    - max_overflow=10: Allow burst connections
    - pool_recycle=300: Recycle connections every 5 min (Neon may close idle connections)
    """
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,
    )


Base = declarative_base()


def _get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = _get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
