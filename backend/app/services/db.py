"""
backend/app/services/db.py
---------------------------
Database engine, session factory, and utility functions.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models.database import Base, AppSettings, DEFAULT_SETTINGS

log = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for a DB session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(drop_all: bool = False):
    """Create all tables and seed default settings."""
    engine = get_engine()
    if drop_all:
        log.warning("Dropping all tables!")
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    log.info("Database tables created/verified.")
    _seed_settings()


def _seed_settings():
    """Insert default settings if they don't exist."""
    with get_db() as session:
        for key, value, description in DEFAULT_SETTINGS:
            existing = session.query(AppSettings).filter_by(key=key).first()
            if not existing:
                session.add(AppSettings(key=key, value=value, description=description))
        log.info("Default settings seeded.")


def get_setting(key: str, default: str = "") -> str:
    """Retrieve a setting value from DB."""
    with get_db() as session:
        row = session.query(AppSettings).filter_by(key=key).first()
        return row.value if row else default


def set_setting(key: str, value: str) -> None:
    """Update a setting value in DB."""
    with get_db() as session:
        row = session.query(AppSettings).filter_by(key=key).first()
        if row:
            row.value = str(value)
        else:
            session.add(AppSettings(key=key, value=str(value)))
