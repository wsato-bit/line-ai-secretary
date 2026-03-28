"""Database connection and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import config


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    pass


def _build_engine():
    """Build SQLAlchemy engine from DATABASE_URL config."""
    url = config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not set in environment variables")
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
