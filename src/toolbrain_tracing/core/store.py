"""
TraceStore implementation using a Strategy Pattern for multiple backends.

This module provides a flexible storage system for agent execution traces,
supporting both SQLite (for development) and PostgreSQL (for production).
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List, Iterator
import logging
import re

import sqlparse
from sqlalchemy import create_engine, func, cast, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError, ProgrammingError, TimeoutError
from sqlalchemy.orm import sessionmaker, Session, selectinload

from toolbrain_tracing.config import settings
from toolbrain_tracing.db.base import Base, Trace, Span, ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class BaseStorageBackend:
    """
    Base class for trace storage backends.

    This class defines the interface that all storage backends must implement.
    It handles SQLAlchemy engine and session setup, and provides the core
    method for adding traces to the database.
    """

    def __init__(self, db_url: str):
        """
        Initialize the storage backend.

        Args:
            db_url (str): SQLAlchemy database connection URL.
        """
        self.db_url = db_url
        self.is_sqlite = db_url.startswith("sqlite")

        engine_kwargs: Dict[str, Any] = {
            "echo": settings.LOG_LEVEL.lower() == "debug",
            "pool_pre_ping": True,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }

        if self.is_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
            engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

        self.engine = create_engine(db_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables defined in the models."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created/verified for %s", self.__class__.__name__)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_trace_from_dict(self, trace_data: Dict[str, Any]) -> str:
        """
        Add a trace to the database from a dictionary (parsed JSON).

        Args:
            trace_data (dict): A dictionary representing a complete trace,
                conforming to the ToolBrain OTLP schema.

        Returns:
            str: The trace_id of the inserted trace.

        Raises:
            ValueError: If the trace_data is invalid or missing required fields.
        """
        trace_id = trace_data.get("trace_id")
        if not trace_id:
            raise ValueError("trace_id is required in trace_data")

        attributes = trace_data.get("attributes") or {}
        system_prompt = attributes.get("system_prompt")
        episode_id = attributes.get("toolbrain.episode.id")

        spans_data = trace_data.get("spans") or []
        trace = Trace(
            id=trace_id,
            system_prompt=system_prompt,
            episode_id=episode_id,
            created_at=datetime.utcnow()
        )

        for span_data in spans_data:
            span = self._create_span_from_dict(span_data, trace_id)
            trace.spans.append(span)

        session = self.get_session()
        try:
            session.add(trace)
            session.commit()
            logger.info("Successfully added trace %s with %s spans", trace_id, len(trace.spans))
            return trace_id
        except IntegrityError:
            session.rollback()
            existing = session.query(Trace.id).filter(Trace.id == trace_id).first()
            if existing:
                logger.info("Trace %s already exists; treating as idempotent insert", trace_id)
                return trace_id
            raise
        except Exception:
            session.rollback()
            logger.exception("Failed to add trace")
            raise
        finally:
            session.close()

    def _create_span_from_dict(self, span_data: Dict[str, Any], trace_id: str) -> Span:
        """Create a Span object from a dictionary."""
        span_id = span_data.get("span_id")
        if not span_id:
            raise ValueError("span_id is required in span_data")

        start_time = self._parse_timestamp(span_data.get("start_time"))
        end_time = self._parse_timestamp(span_data.get("end_time"))

        return Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=span_data.get("parent_id"),
            name=span_data.get("name") or "Unknown",
            start_time=start_time,
            end_time=end_time,
            attributes=span_data.get("attributes") or {}
        )

    @staticmethod
    def _parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse an ISO 8601 timestamp string to a datetime object."""
        if not timestamp_str:
            return None

        match = re.match(
            r"^(?P<base>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?P<frac>\.\d+)?(?P<tz>Z|[+-]\d{2}:?\d{2})?$",
            timestamp_str
        )
        if not match:
            logger.warning("Failed to parse timestamp '%s'", timestamp_str)
            return None

        base = match.group("base")
        frac = match.group("frac") or ""
        tz = match.group("tz") or ""

        if tz == "Z":
            tz = "+00:00"
        if frac:
            frac_digits = frac[1:]
            frac_digits = (frac_digits[:6]).ljust(6, "0")
            frac = f".{frac_digits}"

        normalized = f"{base}{frac}{tz}"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            logger.warning("Failed to parse timestamp '%s'", timestamp_str)
            return None

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve a trace by its ID."""
        session = self.get_session()
        try:
            return (
                session.query(Trace)
                .options(selectinload(Trace.spans))
                .filter(Trace.id == trace_id)
                .first()
            )
        finally:
            session.close()

    def list_traces(self, limit: int = 100, skip: int = 0, include_spans: bool = False) -> List[Trace]:
        """List traces in the database with pagination."""
        session = self.get_session()
        try:
            query = session.query(Trace).order_by(Trace.created_at.desc()).offset(skip).limit(limit)
            if include_spans:
                query = query.options(selectinload(Trace.spans))
            return query.all()
        finally:
            session.close()

    def get_traces_by_episode_id(self, episode_id: str) -> List[Trace]:
        """Get all traces for a specific episode ID."""
        session = self.get_session()
        try:
            return (
                session.query(Trace)
                .options(selectinload(Trace.spans))
                .filter(Trace.episode_id == episode_id)
                .order_by(Trace.created_at.desc())
                .all()
            )
        finally:
            session.close()

    def execute_read_only_sql(self, query: str, row_limit: int = 100) -> Dict[str, Any]:
        """Execute a read-only SQL query with defense-in-depth controls."""
        try:
            parsed = sqlparse.parse(query)
            if not parsed or parsed[0].get_type() != "SELECT":
                raise ValueError("Only SELECT statements are permitted.")
        except Exception as e:
            return {"error": f"SQL Parsing Error: {str(e)}"}

        try:
            with self.get_session() as session:
                if self.engine.dialect.name == "postgresql":
                    session.execute(text("SET LOCAL statement_timeout = 5000;"))
                    session.execute(text("SET LOCAL TRANSACTION READ ONLY;"))

                result = session.execute(text(query))
                column_names = list(result.keys())
                rows = [
                    dict(zip(column_names, row))
                    for row in result.fetchmany(row_limit)
                ]
                return {"rows": rows, "count": len(rows)}

        except TimeoutError:
            return {
                "error": "SQL Execution Error: The query took too long to execute and was timed out. Please write a more efficient query."
            }
        except ProgrammingError as e:
            return {"error": f"SQL Execution Error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error in execute_read_only_sql: %s", e, exc_info=True)
            return {"error": "An unexpected internal error occurred."}

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a session ordered by created_at."""
        session = self.get_session()
        try:
            messages = (
                session.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            return [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at,
                }
                for message in messages
            ]
        finally:
            session.close()

    def save_chat_message(self, session_id: str, role: str, content: str) -> None:
        """Save a new chat message, creating the session if needed."""
        session = self.get_session()
        try:
            chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                chat_session = ChatSession(id=session_id)
                session.add(chat_session)

            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
            )
            session.add(message)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Failed to save chat message")
            raise
        finally:
            session.close()

    def count_traces(self) -> int:
        """Return total trace count."""
        session = self.get_session()
        try:
            return int(session.query(func.count(Trace.id)).scalar() or 0)
        finally:
            session.close()

    def add_feedback(self, trace_id: str, feedback_data: Dict[str, Any]) -> bool:
        """Add or update feedback for a trace."""
        session = self.get_session()
        try:
            updated = (
                session.query(Trace)
                .filter(Trace.id == trace_id)
                .update({"feedback": feedback_data})
            )
            if updated == 0:
                raise ValueError(f"Trace with ID '{trace_id}' not found")
            session.commit()
            logger.info("Added feedback to trace %s", trace_id)
            return True
        except Exception:
            session.rollback()
            logger.exception("Failed to add feedback")
            raise
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the TraceStore."""
        from datetime import timedelta

        session = self.get_session()
        try:
            total_traces = session.query(func.count(Trace.id)).scalar() or 0
            total_spans = session.query(func.count(Span.id)).scalar() or 0
            if self.engine.dialect.name == "postgresql":
                rating_value = func.jsonb_extract_path_text(
                    cast(Trace.feedback, JSONB),
                    "rating",
                )
                traces_with_feedback = (
                    session.query(func.count(Trace.id))
                    .filter(Trace.feedback.isnot(None))
                    .filter(rating_value.isnot(None))
                    .scalar()
                    or 0
                )
            else:
                traces_with_feedback = (
                    session.query(func.count(Trace.id))
                    .filter(Trace.feedback.isnot(None))
                    .filter(Trace.feedback != {})
                    .scalar()
                    or 0
                )

            yesterday = datetime.utcnow() - timedelta(days=1)
            traces_last_24h = (
                session.query(func.count(Trace.id))
                .filter(Trace.created_at >= yesterday)
                .scalar()
                or 0
            )

            avg_spans = total_spans / total_traces if total_traces > 0 else 0

            return {
                "total_traces": int(total_traces),
                "total_spans": int(total_spans),
                "traces_with_feedback": int(traces_with_feedback),
                "traces_last_24h": int(traces_last_24h),
                "avg_spans_per_trace": round(avg_spans, 2)
            }
        finally:
            session.close()

    def get_tool_usage_stats(self, limit: int = 10) -> Dict[str, Any]:
        """Get tool usage statistics from all traces."""
        session = self.get_session()
        try:
            if self.engine.dialect.name == "postgresql":
                span_type = func.jsonb_extract_path_text(Span.attributes, "toolbrain.span.type")
                tool_name = func.jsonb_extract_path_text(Span.attributes, "toolbrain.tool.name")
                rows = (
                    session.query(tool_name.label("tool"), func.count().label("count"))
                    .filter(span_type == "tool_execution")
                    .filter(tool_name.isnot(None))
                    .group_by(tool_name)
                    .order_by(func.count().desc())
                    .limit(limit)
                    .all()
                )
                tools = [{"tool": row.tool, "count": int(row.count)} for row in rows]
                total_tool_calls = sum(item["count"] for item in tools)
                return {"tools": tools, "total_tool_calls": total_tool_calls}

            spans = session.query(Span.attributes).all()
            tool_counts: Dict[str, int] = {}
            for (attrs,) in spans:
                attrs = attrs or {}
                if attrs.get("toolbrain.span.type") != "tool_execution":
                    continue
                tool = attrs.get("toolbrain.tool.name")
                if not tool:
                    continue
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

            tools = [
                {"tool": tool, "count": count}
                for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            ]
            return {"tools": tools, "total_tool_calls": sum(tool_counts.values())}
        finally:
            session.close()


class SQLiteBackend(BaseStorageBackend):
    """SQLite storage backend for development and testing."""

    def __init__(self, db_url: str = "sqlite:///tracestore.db"):
        super().__init__(db_url)
        logger.info("SQLite backend initialized: %s", db_url)


class PostgresBackend(BaseStorageBackend):
    """PostgreSQL storage backend for production."""

    def __init__(self, db_url: str):
        if not db_url:
            raise ValueError("db_url is required for PostgreSQL backend")
        super().__init__(db_url)
        logger.info("PostgreSQL backend initialized")


class TraceStore:
    """Factory class for creating trace storage backends."""

    def __new__(cls, backend: str = "sqlite", db_url: Optional[str] = None):
        backend = backend.lower()
        if backend == "sqlite":
            db_url = db_url or "sqlite:///tracestore.db"
            return SQLiteBackend(db_url=db_url)

        if backend in {"postgres", "postgresql"}:
            if not db_url:
                raise ValueError(
                    "db_url is required for PostgreSQL backend. "
                    "Example: 'postgresql://user:password@localhost/tracestore'"
                )
            return PostgresBackend(db_url=db_url)

        raise ValueError(
            f"Unknown backend: {backend}. Supported backends: 'sqlite', 'postgres'"
        )
