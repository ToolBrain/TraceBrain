"""
Database Session Management Utilities

This module provides optional utilities for direct database session management.
Currently, the TraceStore class in core.store handles all session management
using the Strategy pattern. This module can be used for future extensions that
require direct database access patterns (e.g., FastAPI dependency injection).

Usage:
    from toolbrain_tracing.db.session import get_session_maker
    
    # Get a session maker for direct database access
    SessionLocal = get_session_maker()
    session = SessionLocal()
    try:
        # Perform database operations
        traces = session.query(Trace).all()
    finally:
        session.close()
        
    # Or use dependency injection in FastAPI:
    from toolbrain_tracing.db.session import get_db
    
    @app.get("/custom")
    def custom_endpoint(db: Session = Depends(get_db)):
        traces = db.query(Trace).all()
        return traces
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from .base import Base


# Global variables for engine and session maker
_engine = None
_SessionLocal = None


def get_engine():
    """
    Get or create the SQLAlchemy engine.
    
    This function creates a singleton engine instance based on the
    DATABASE_URL from settings.
    
    Returns:
        Engine: SQLAlchemy engine instance.
    """
    global _engine
    if _engine is None:
        connect_args = {}
        if settings.is_sqlite:
            connect_args = {"check_same_thread": False}

        _engine = create_engine(
            settings.DATABASE_URL,
            echo=(settings.LOG_LEVEL.lower() == "debug"),
            pool_pre_ping=True,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            connect_args=connect_args
        )
    return _engine


def get_session_maker():
    """
    Get or create the SQLAlchemy session factory.
    
    Returns:
        sessionmaker: SQLAlchemy session factory.
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    This function can be used with FastAPI's Depends() for dependency injection.
    It ensures proper session lifecycle management with automatic cleanup.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    
    Yields:
        Session: SQLAlchemy database session.
    """
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    
    This function creates all tables defined in the ORM models.
    It's idempotent and safe to call multiple times.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use only for testing or reset purposes.
    """
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
