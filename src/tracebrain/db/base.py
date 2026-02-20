"""
SQLAlchemy ORM models for TraceBrain trace storage.

This module defines the database schema for storing agent execution traces
conforming to the TraceBrain Standard OTLP Trace Schema.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Index, Text, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON, TypeDecorator

from pgvector.sqlalchemy import Vector

Base = declarative_base()


class JSONBCompat(TypeDecorator):
    """
    JSON type that uses JSONB for PostgreSQL and JSON for other databases.
    
    This allows us to use JSONB's superior indexing and querying capabilities
    on PostgreSQL while falling back to standard JSON for SQLite and other
    databases.
    """
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class VectorCompat(TypeDecorator):
    """Vector type that uses pgvector for PostgreSQL and JSON for other databases."""

    impl = JSON
    cache_ok = True

    try:
        comparator_factory = Vector.comparator_factory
    except AttributeError:
        comparator_factory = getattr(Vector, "Comparator", None)

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())


class TraceStatus(str, Enum):
    running = "running"
    completed = "completed"
    needs_review = "needs_review"
    failed = "failed"


class Trace(Base):
    """
    Represents a complete agent execution trace.
    
    A trace contains metadata about the agent's execution context and
    a collection of spans representing individual steps (LLM inferences,
    tool executions, etc.).
    
    Attributes:
        id (str): The unique trace_id from the OTLP trace (primary key).
        system_prompt (str): The system prompt used for the agent.
        created_at (datetime): Timestamp when the trace was created.
        feedback (dict): Optional user feedback (rating, comments, etc.).
        spans (list[Span]): Collection of spans belonging to this trace.
    """
    __tablename__ = "traces"
    
    id = Column(String, primary_key=True, comment="Trace ID from OTLP trace")
    system_prompt = Column(Text, nullable=True, comment="System prompt for the agent")
    episode_id = Column(
        String,
        nullable=True,
        index=True,
        comment="Episode identifier grouping multiple traces"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when trace was created"
    )
    status = Column(
        SAEnum(TraceStatus, name="trace_status", native_enum=False),
        default=TraceStatus.running,
        nullable=False,
        comment="Trace status: running|completed|needs_review|failed",
    )
    priority = Column(
        Integer,
        nullable=True,
        default=3,
        comment="Priority level (1-5)",
    )
    embedding = Column(
        VectorCompat(384),
        nullable=True,
        comment="Trace embedding vector",
    )
    attributes = Column(
        JSONBCompat,
        nullable=True,
        default=dict,
        comment="Trace-level attributes (episode ID, AI eval, etc.)",
    )
    feedback = Column(
        JSONBCompat,
        nullable=True,
        default=None,
        comment="User feedback on trace quality (rating, comments, etc.)"
    )
    ai_evaluation = Column(
        JSONBCompat,
        nullable=True,
        default=None,
        comment="AI evaluation metadata (rating, confidence, status, feedback)"
    )
    
    # Relationship to spans
    spans = relationship(
        "Span",
        back_populates="trace",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        Index("idx_trace_created_at", "created_at"),
        Index("idx_trace_episode_id", "episode_id"),
        Index("idx_trace_attributes_gin", "attributes", postgresql_using="gin"),
        Index("idx_trace_feedback_gin", "feedback", postgresql_using="gin"),
        Index("idx_trace_ai_eval_gin", "ai_evaluation", postgresql_using="gin"),
    )
    
    def __repr__(self):
        return (
            f"<Trace(id='{self.id}', episode_id='{self.episode_id}', "
            f"status='{self.status}', spans={len(self.spans)})>"
        )


class Span(Base):
    """
    Represents a single step in an agent execution trace.
    
    Spans capture individual operations like LLM inferences or tool executions.
    They form a hierarchy through parent-child relationships and store flexible
    custom attributes in JSONB format.
    
    Attributes:
        id (int): Internal database ID (auto-incremented primary key).
        span_id (str): The unique span_id from the OTLP trace.
        trace_id (str): Foreign key reference to the parent trace.
        parent_id (str): The span_id of the parent span (null for root spans).
        name (str): Human-readable name describing the operation.
        start_time (datetime): When the operation started.
        end_time (datetime): When the operation completed.
        attributes (dict): JSONBCompat column storing custom TraceBrain attributes.
        trace (Trace): Relationship back to the parent trace.
    """
    __tablename__ = "spans"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Internal DB ID")
    span_id = Column(
        String,
        nullable=False,
        index=True,
        comment="Span ID from OTLP trace (unique per trace)"
    )
    trace_id = Column(
        String,
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent trace"
    )
    parent_id = Column(
        String,
        nullable=True,
        index=True,
        comment="Parent span ID for hierarchical tracing"
    )
    name = Column(String, nullable=False, comment="Human-readable operation name")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="Operation start timestamp")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="Operation end timestamp")
    
    # JSONBCompat automatically uses JSONB for PostgreSQL, JSON for SQLite
    # This stores all custom TraceBrain attributes (tracebrain.*)
    attributes = Column(
        JSONBCompat,
        nullable=False,
        default=dict,
        comment="Custom TraceBrain semantic attributes"
    )
    
    # Relationship to trace
    trace = relationship("Trace", back_populates="spans")
    
    # Composite index for efficient queries
    __table_args__ = (
        UniqueConstraint("trace_id", "span_id", name="uq_span_trace_spanid"),
        Index("idx_span_trace_parent", "trace_id", "parent_id"),
        Index("idx_span_trace_time", "trace_id", "start_time"),
        Index("idx_span_attributes_gin", "attributes", postgresql_using="gin"),
    )
    
    def __repr__(self):
        return f"<Span(span_id='{self.span_id}', name='{self.name}', trace_id='{self.trace_id}')>"


class ChatSession(Base):
    """Represents a chat session for conversational memory."""

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, comment="Chat session ID (UUID)")
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when session was created",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select",
    )


class ChatMessage(Base):
    """Represents a single message in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Message ID")
    session_id = Column(
        String,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="Parent chat session ID",
    )
    role = Column(String, nullable=False, comment="Message role: user|assistant|tool")
    content = Column(Text, nullable=False, comment="Message content")
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when message was created",
    )

    session = relationship("ChatSession", back_populates="messages")


class History(Base):
    """Represents users TraceBrain browsing history."""
    __tablename__ = "history"

    id = Column(String, primary_key=True, comment="Trace or episode ID")
    type = Column(String, nullable=False, comment="'trace' or 'episode'")
    last_accessed = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Most recent access timestamp"
    )

    __table_args__ = (
        Index("idx_accessed", "last_accessed"),
    )


class AppSettings(Base):
    """Singleton application settings storage (global config)."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, comment="Singleton row ID")
    config = Column(
        JSONBCompat,
        nullable=False,
        default=dict,
        comment="Global settings JSON payload",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )
    
class CurriculumTask(Base):
    """Represents a generated training task for the automated curriculum."""

    __tablename__ = "curriculum_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Task ID")
    task_description = Column(String, nullable=False, comment="Suggested training task")
    reasoning = Column(Text, nullable=False, comment="Why this task was suggested")
    status = Column(String, nullable=False, default="pending", comment="pending|completed")
    priority = Column(String, nullable=False, default="medium", comment="high|medium|low")
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when task was created",
    )
