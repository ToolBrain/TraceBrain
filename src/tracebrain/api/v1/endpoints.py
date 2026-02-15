"""
TraceBrain TraceStore REST API Endpoints (v1)

This module provides FastAPI router with endpoints for interacting with the TraceStore.
It exposes endpoints for querying traces, retrieving trace details, and adding feedback.

Features:
- GET /api/v1/health: Health check
- GET /api/v1/traces: List all traces with pagination
- GET /api/v1/traces/{trace_id}: Get detailed trace information
- POST /api/v1/traces: Ingest a trace
- POST /api/v1/traces/init: Initialize a trace before spans are available
- POST /api/v1/ops/batch_evaluate: Batch AI evaluation
- POST /api/v1/traces/{trace_id}/feedback: Add user feedback to a trace
- POST /api/v1/traces/{trace_id}/signal: Mark a trace as needs review
- GET /api/v1/traces/search: Semantic experience search
- GET /api/v1/export/traces: Export traces
- GET /api/v1/episodes/{episode_id}: Retrieve episode summary
- GET /api/v1/stats: Get database statistics
- GET /api/v1/analytics/tool_usage: Get tool usage analytics
- POST /api/v1/ai_evaluate/{trace_id}: Evaluate a trace with AI judge
- POST /api/v1/natural_language_query: AI-powered natural language queries
- GET /api/v1/librarian_sessions/{session_id}: Retrieve librarian chat history
- POST /api/v1/curriculum/generate: Generate curriculum tasks
- GET /api/v1/curriculum: List curriculum tasks
- GET /api/v1/curriculum/export: Export curriculum tasks
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid
import json

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_serializer, ConfigDict

from sqlalchemy import func, cast, Integer
from sqlalchemy.dialects.postgresql import JSONB

from ...core.store import TraceStore
from ...core.curator import CurriculumCurator
from ...db.base import TraceStatus, CurriculumTask, Trace
from ...evaluators.judge_agent import AIJudge
from ...core.librarian import LibrarianAgent, LIBRARIAN_AVAILABLE
from ...config import settings

# Initialize APIRouter instead of FastAPI app
router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize TraceStore with settings from config
store = TraceStore(
    backend=settings.get_backend_type(),
    db_url=settings.DATABASE_URL
)

# Initialize Librarian Agent (lazy loading)
_librarian_agent = None


def get_librarian_agent():
    """Lazy initialization of Librarian agent."""
    global _librarian_agent
    if _librarian_agent is None:
        _librarian_agent = LibrarianAgent(store)
    return _librarian_agent


# ============================================================================
# Pydantic Models for API Schema
# ============================================================================
    
class FeedbackOut(BaseModel):
    """Response model for feedback data."""
    
    rating: Optional[int] = Field(None, description="Rating from 1-5")
    comment: Optional[str] = Field(None, description="Text comment or feedback")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    timestamp: Optional[str] = Field(None, description="When feedback was added")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "comment": "Great reasoning!",
                "tags": ["high-quality"],
                "timestamp": "2025-12-11T15:35:00Z",
                "metadata": {"reviewer": "user123"}
            }
        }
    )


class SpanOut(BaseModel):
    """Response model for a single span."""
    
    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[datetime] = Field(None, description="Operation start timestamp")
    end_time: Optional[datetime] = Field(None, description="Operation end timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom TraceBrain attributes")
    
    @field_serializer('start_time', 'end_time')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Convert datetime to ISO 8601 string for JSON serialization."""
        return dt.isoformat() if dt else None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "span_id": "1001a2b3c4d5e6f7",
                "parent_id": None,
                "name": "LLM Inference (Tool Call)",
                "start_time": "2025-11-20T10:00:01.000Z",
                "end_time": "2025-11-20T10:00:02.500Z",
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.thought": "I should use the calculator tool",
                    "tracebrain.llm.tool_code": "calculator({'expression': '2+2'})"
                }
            }
        }
    )


class TraceOut(BaseModel):
    """Response model for a trace (OTLP Schema compliant)."""
    
    trace_id: str = Field(..., description="Unique trace identifier")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trace-level attributes including system_prompt and episode_id"
    )
    created_at: datetime = Field(..., description="Timestamp when trace was created")
    feedbacks: List[FeedbackOut] = Field(default_factory=list, description="List of user feedback on trace quality")
    spans: List[SpanOut] = Field(default_factory=list, description="List of spans in this trace")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "trace_id": "a1b2c3d4e5f6a7b8",
                "attributes": {
                    "system_prompt": "You are a helpful assistant.",
                    "tracebrain.episode.id": "episode_123"
                },
                "created_at": "2025-12-11T15:30:00Z",
                "feedbacks": [{"rating": 5, "comment": "Excellent trace!"}],
                "spans": []
            }
        }
    )


class TraceListOut(BaseModel):
    """Response model for trace list with metadata."""
    
    total: int = Field(..., description="Total number of traces returned")
    skip: int = Field(..., description="Number of traces skipped")
    limit: int = Field(..., description="Maximum number of traces requested")
    traces: List[TraceOut] = Field(..., description="List of traces")

class FeedbackIn(BaseModel):
    """Request model for adding feedback to a trace."""
    
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5")
    comment: Optional[str] = Field(None, description="Text comment or feedback")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "comment": "Great reasoning! The agent handled the multi-step task perfectly.",
                "tags": ["high-quality", "multi-step"],
                "metadata": {"reviewer": "user123", "session_id": "abc"}
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    trace_id: str = Field(..., description="The trace ID that was updated")


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries."""
    query: str = Field(..., description="Natural language question about traces")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    model_id: Optional[str] = Field(None, description="Override LLM model for this request (e.g., 'gemini-2.0-flash-exp', 'gpt-4o')")


class Suggestion(BaseModel):
    label: str
    value: str


class NaturalLanguageResponse(BaseModel):
    """Response model for natural language queries."""
    answer: str = Field(..., description="The AI's answer")
    session_id: str = Field(..., description="Conversation session ID")
    suggestions: Optional[List[Suggestion]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list, description="Trace IDs referenced in the answer")


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class ChatHistoryOut(BaseModel):
    session_id: str
    messages: List[ChatMessageOut]


class TraceSummaryOut(BaseModel):
    """Summary model for a trace inside an episode."""
    trace_id: str
    status: str
    duration_ms: float
    span_count: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class EpisodeOut(BaseModel):
    """Details for an episode containing multiple traces details."""
    episode_id: str
    traces: List[TraceSummaryOut]

class EpisodeTracesOut(BaseModel):
    """Details for an episode containing multiple traces."""
    episode_id: str
    traces: List[TraceOut]


class AIEvaluationIn(BaseModel):
    judge_model_id: str


class AIEvaluationOut(BaseModel):
    rating: int = Field(..., ge=0, le=5, description="Rating from 0-5")
    feedback: str = Field(..., description="AI judge feedback")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Judge confidence score")
    status: Optional[str] = Field(None, description="Evaluation status")
    timestamp: Optional[str] = Field(None, description="When the evaluation was recorded")


class TraceSignalIn(BaseModel):
    reason: str = Field(..., description="Issue description (looping, low confidence, etc.)")


class ExperienceSearchOut(BaseModel):
    trace_id: str
    score: Optional[float] = None
    rating: Optional[int] = None
    feedback: Optional[Dict[str, Any]] = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class ExperienceSearchResponse(BaseModel):
    total: int
    results: List[ExperienceSearchOut]


class CurriculumTaskOut(BaseModel):
    id: int
    task_description: str
    reasoning: str
    status: str
    priority: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


# Request models for trace ingestion
class SpanIn(BaseModel):
    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    end_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom TraceBrain attributes")


class TraceIn(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Trace-level attributes")
    spans: List[SpanIn] = Field(default_factory=list, description="Ordered list of spans")


class TraceIngestResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    trace_id: str = Field(..., description="The trace ID that was stored")
    message: str = Field(..., description="Status message")


class TraceInitIn(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    episode_id: Optional[str] = Field(None, description="Episode identifier")
    system_prompt: Optional[str] = Field(None, description="System prompt used by the agent")


def _trace_to_out(trace) -> TraceOut:
    span_outs = []
    for span in trace.spans:
        span_data = SpanOut.model_validate(span)
        if trace.system_prompt:
            span_data.attributes["system_prompt"] = trace.system_prompt
        span_outs.append(span_data)

    feedbacks = []
    if trace.feedback:
        feedbacks = [FeedbackOut(**trace.feedback)]

    trace_attributes: Dict[str, Any] = {}
    if trace.system_prompt:
        trace_attributes["system_prompt"] = trace.system_prompt
    if trace.episode_id:
        trace_attributes["tracebrain.episode.id"] = trace.episode_id
    if trace.status:
        trace_attributes["tracebrain.trace.status"] = (
            trace.status.value if hasattr(trace.status, "value") else str(trace.status)
        )
    if trace.priority is not None:
        trace_attributes["tracebrain.trace.priority"] = trace.priority
    if trace.ai_evaluation:
        trace_attributes["tracebrain.ai_evaluation"] = trace.ai_evaluation

    return TraceOut(
        trace_id=trace.id,
        attributes=trace_attributes,
        created_at=trace.created_at,
        feedbacks=feedbacks,
        spans=span_outs
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/", tags=["Root"])
def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "TraceBrain TraceStore API",
        "version": "1.0.0",
        "description": "REST API for managing agent execution traces",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /api/v1/health",
            "list_traces": "GET /api/v1/traces",
            "get_trace": "GET /api/v1/traces/{trace_id}",
            "ingest_trace": "POST /api/v1/traces",
            "batch_evaluate": "POST /api/v1/ops/batch_evaluate",
            "init_trace": "POST /api/v1/traces/init",
            "add_feedback": "POST /api/v1/traces/{trace_id}/feedback",
            "signal_trace": "POST /api/v1/traces/{trace_id}/signal",
            "search_traces": "GET /api/v1/traces/search",
            "export_traces": "GET /api/v1/export/traces",
            "get_episode": "GET /api/v1/episodes/{episode_id}",
            "stats": "GET /api/v1/stats",
            "tool_usage": "GET /api/v1/analytics/tool_usage",
            "ai_evaluate": "POST /api/v1/ai_evaluate/{trace_id}",
            "natural_language_query": "POST /api/v1/natural_language_query",
            "librarian_session": "GET /api/v1/librarian_sessions/{session_id}",
            "curriculum_generate": "POST /api/v1/curriculum/generate",
            "curriculum_list": "GET /api/v1/curriculum",
            "curriculum_export": "GET /api/v1/curriculum/export"
        }
    }


@router.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify API and database connectivity.
    """
    try:
        # Try to query the database
        store.list_traces(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "backend": settings.get_backend_type(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/traces", response_model=TraceListOut, tags=["Traces"])
def list_traces(
    skip: int = Query(0, ge=0, description="Number of traces to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of traces to return")
):
    """
    List all traces with pagination.
    
    Returns traces ordered by creation time (most recent first).
    """
    try:
        # Get traces from store with pagination
        traces = store.list_traces(limit=limit, skip=skip, include_spans=True)
        total = store.count_traces()

        trace_outs = [_trace_to_out(trace) for trace in traces]

        return TraceListOut(
            total=total,
            skip=skip,
            limit=limit,
            traces=trace_outs
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list traces: {str(e)}"
        )


@router.get("/traces/search", response_model=ExperienceSearchResponse, tags=["Traces"])
def search_traces(
    text: str = Query(..., description="Natural language search text"),
    min_rating: int = Query(4, ge=1, le=5, description="Minimum rating threshold"),
    limit: int = Query(3, ge=1, le=20, description="Maximum number of results"),
):
    """Search for similar high-quality traces using vector similarity."""
    try:
        results = store.search_similar_experiences(text, min_rating=min_rating, limit=limit)
        return ExperienceSearchResponse(total=len(results), results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search traces: {str(e)}")


@router.get("/export/traces", tags=["Export"])
def export_traces(
    min_rating: int = Query(4, ge=1, le=5, description="Minimum rating threshold"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of traces"),
    format: str = Query("json", description="Export format: 'json' or 'jsonl'"),
):
    """Export high-quality traces as OTLP payloads."""
    format_value = format.lower().strip()
    if format_value not in {"json", "jsonl"}:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'jsonl'.")
    session = store.get_session()
    try:
        results: List[Dict[str, Any]] = []
        if settings.is_postgres:
            rating_value = cast(
                func.jsonb_extract_path_text(cast(Trace.feedback, JSONB), "rating"),
                Integer,
            )
            trace_rows = (
                session.query(Trace)
                .filter(Trace.feedback.isnot(None))
                .filter(rating_value >= min_rating)
                .order_by(Trace.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            trace_rows = session.query(Trace).order_by(Trace.created_at.desc()).all()
            filtered = []
            for trace in trace_rows:
                rating = None
                if trace.feedback and isinstance(trace.feedback, dict):
                    rating = trace.feedback.get("rating")
                if isinstance(rating, int) and rating >= min_rating:
                    filtered.append(trace)
            trace_rows = filtered[:limit]

        for trace in trace_rows:
            otlp = store.get_full_trace(trace.id)
            if otlp:
                results.append(otlp)

        if format_value == "jsonl":
            jsonl_content = "\n".join(json.dumps(item) for item in results)
            return Response(content=jsonl_content, media_type="application/x-jsonlines")

        return results
    finally:
        session.close()


@router.get("/traces/{trace_id}", response_model=TraceOut, tags=["Traces"])
def get_trace(trace_id: str):
    """
    Get detailed information for a specific trace.
    
    Args:
        trace_id: The unique identifier of the trace.
    
    Returns:
        Complete trace information including all spans and attributes.
    
    Raises:
        404: If the trace is not found.
    """
    try:
        trace = store.get_trace(trace_id)
        
        if not trace:
            raise HTTPException(
                status_code=404,
                detail=f"Trace with ID '{trace_id}' not found"
            )
        
        return _trace_to_out(trace)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve trace: {str(e)}"
        )


@router.post("/traces", response_model=TraceIngestResponse, status_code=status.HTTP_201_CREATED, tags=["Traces"])
def ingest_trace(trace: TraceIn):
    """
    Ingest a trace into the TraceStore.
    """
    try:
        trace_id = store.add_trace_from_dict(trace.model_dump())
        return TraceIngestResponse(
            success=True,
            trace_id=trace_id,
            message="Trace stored successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store trace: {str(e)}")


@router.post("/traces/init", response_model=TraceIngestResponse, status_code=status.HTTP_201_CREATED, tags=["Traces"])
def init_trace(trace: TraceInitIn):
    """Pre-register a trace before spans are available."""
    try:
        trace_id = store.init_trace(
            trace_id=trace.trace_id,
            episode_id=trace.episode_id,
            system_prompt=trace.system_prompt,
        )
        return TraceIngestResponse(
            success=True,
            trace_id=trace_id,
            message="Trace initialized successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize trace: {str(e)}")


@router.post("/traces/{trace_id}/feedback", response_model=FeedbackResponse, tags=["Feedback"])
def add_feedback(trace_id: str, feedback: FeedbackIn):
    """
    Add or update feedback for a specific trace.
    
    Args:
        trace_id: The unique identifier of the trace.
        feedback: Feedback data including rating, comments, tags, etc.
    
    Returns:
        Success confirmation with trace ID.
    
    Raises:
        404: If the trace is not found.
        500: If the operation fails.
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        feedback_data = feedback.model_dump(exclude_none=True)
        
        # Add timestamp
        feedback_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Store feedback
        store.add_feedback(trace_id, feedback_data)

        session = store.get_session()
        try:
            trace = session.query(Trace).filter(Trace.id == trace_id).first()
            if trace and trace.ai_evaluation:
                updated = dict(trace.ai_evaluation)
                updated["status"] = "completed"
                updated["timestamp"] = datetime.utcnow().isoformat()
                trace.ai_evaluation = updated
                trace.status = TraceStatus.completed
                session.commit()
        finally:
            session.close()
        
        return FeedbackResponse(
            success=True,
            message="Feedback added successfully",
            trace_id=trace_id
        )
        
    except ValueError as e:
        # Trace not found
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add feedback: {str(e)}"
        )


@router.post("/ops/batch_evaluate", tags=["Operations"])
def batch_evaluate_traces(
    limit: int = Query(5, ge=1, le=50, description="Max traces to evaluate per call"),
):
    """Evaluate recent traces without AI evaluations and attach scores."""
    session = store.get_session()
    judge = AIJudge(store)
    processed = 0
    failed = 0
    errors: List[Dict[str, str]] = []
    try:
        traces = (
            session.query(Trace)
            .filter(Trace.ai_evaluation.is_(None))
            .order_by(Trace.created_at.desc())
            .limit(limit)
            .all()
        )

        for trace in traces:
            try:
                result = judge.evaluate(trace.id, settings.LLM_MODEL)
                confidence = float(result["confidence"])
                status_value = "auto_verified" if confidence > 0.8 else "pending_review"
                ai_eval = {
                    "rating": result["rating"],
                    "feedback": result["feedback"],
                    "confidence": confidence,
                    "status": status_value,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                trace.ai_evaluation = dict(ai_eval)
                processed += 1
            except Exception as exc:
                failed += 1
                logger.exception("Batch evaluate failed for trace %s", trace.id)
                errors.append({"trace_id": trace.id, "error": str(exc)})

        session.commit()
        return {"success": True, "processed": processed, "failed": failed, "errors": errors}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch evaluate traces: {str(e)}")
    finally:
        session.close()


@router.post("/traces/{trace_id}/signal", response_model=FeedbackResponse, tags=["Governance"])
def signal_trace_issue(trace_id: str, payload: TraceSignalIn):
    """Mark a trace as needing review based on an agent signal."""
    try:
        store.update_trace_status(trace_id, TraceStatus.needs_review)
        logger.info("Trace %s flagged for review: %s", trace_id, payload.reason)
        return FeedbackResponse(
            success=True,
            message="Trace flagged for review",
            trace_id=trace_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to signal trace: {str(e)}")


@router.post("/curriculum/generate", tags=["Curriculum"])
def generate_curriculum():
    """Generate curriculum tasks from failed traces."""
    try:
        curator = CurriculumCurator(store)
        created = curator.generate_curriculum()
        return {"status": "success", "tasks_generated": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {str(e)}")


@router.get("/curriculum", response_model=List[CurriculumTaskOut], tags=["Curriculum"])
def list_curriculum_tasks():
    """List all curriculum tasks ordered by creation time."""
    session = store.get_session()
    try:
        return (
            session.query(CurriculumTask)
            .order_by(CurriculumTask.created_at.desc())
            .all()
        )
    finally:
        session.close()


@router.get("/curriculum/export", tags=["Curriculum"])
def export_curriculum(
    format: str = Query("json", description="Export format: 'json' or 'jsonl'"),
):
    """Export pending curriculum tasks for training ingestion."""
    format_value = format.lower().strip()
    if format_value not in {"json", "jsonl"}:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'jsonl'.")
    try:
        tasks = store.get_pending_curriculum(limit=100)

        export_data = []
        for task in tasks:
            export_data.append(
                {
                    "id": task["id"],
                    "role": "user",
                    "content": task["instruction"],
                    "metadata": {
                        "difficulty": task["priority"],
                        "focus": "auto_curriculum",
                        "reasoning": task["context"],
                    },
                }
            )

        if format_value == "jsonl":
            jsonl_content = "\n".join(json.dumps(item) for item in export_data)
            return Response(content=jsonl_content, media_type="application/x-jsonlines")

        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodes/{episode_id}", response_model=EpisodeOut, tags=["Episodes"])
def get_episode_details(episode_id: str):
    """Get episode details including the list of traces in that episode."""
    try:
        traces_in_episode = store.get_traces_by_episode_id(episode_id)

        if not traces_in_episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        trace_summaries: List[TraceSummaryOut] = []
        for trace in traces_in_episode:
            spans = trace.spans or []
            span_count = len(spans)

            start_times = [span.start_time for span in spans if span.start_time]
            end_times = [span.end_time for span in spans if span.end_time]
            duration_ms = 0.0
            if start_times and end_times:
                duration_ms = (max(end_times) - min(start_times)).total_seconds() * 1000

            status = "OK"
            for span in spans:
                name = (span.name or "").lower()
                span_type = (span.attributes or {}).get("tracebrain.span.type")
                if "error" in name or span_type == "tool_error":
                    status = "ERROR"
                    break

            trace_summaries.append(
                TraceSummaryOut(
                    trace_id=trace.id,
                    status=status,
                    duration_ms=round(duration_ms, 2),
                    span_count=span_count,
                    created_at=trace.created_at
                )
            )

        return EpisodeOut(episode_id=episode_id, traces=trace_summaries)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/episodes/{episode_id}/traces", response_model=EpisodeTracesOut, tags=["Episodes"])
def get_episode_traces(episode_id: str):
    """Get all traces related to an episode"""
    try:
        traces_in_episode = store.get_traces_by_episode_id(episode_id)
        if not traces_in_episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        trace_ids = [trace.id for trace in traces_in_episode]
        traces = store.get_traces_by_ids(trace_ids, include_spans=True)
        trace_outs = [_trace_to_out(trace) for trace in traces]
        return EpisodeTracesOut(episode_id=episode_id, traces=trace_outs)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/stats", tags=["Analytics"])
def get_stats():
    """
    Get overall statistics about the TraceStore.
    
    Returns:
        Dictionary with key metrics including total traces, spans, etc.
    """
    try:
        return store.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/analytics/tool_usage", tags=["Analytics"])
def get_tool_usage(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of tools to return")
):
    """
    Get tool usage statistics from all traces.
    
    Args:
        limit: Maximum number of tools to return (top N).
    
    Returns:
        List of tool names with their usage counts.
    """
    try:
        return store.get_tool_usage_stats(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve tool usage: {str(e)}"
        )


# ============================================================================
# AI-Powered Endpoints
# ============================================================================

@router.get("/librarian_sessions/{session_id}", response_model=ChatHistoryOut, tags=["AI"])
def get_librarian_session(session_id: str):
    """Fetch the stored chat history for a Librarian session."""
    try:
        messages = store.get_chat_history(session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Session not found")

        return ChatHistoryOut(session_id=session_id, messages=messages)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(e)}")


@router.post("/natural_language_query", response_model=NaturalLanguageResponse, tags=["AI"])
def natural_language_query(query: NaturalLanguageQuery):
    """
    Process a natural language query about traces using the configured LLM provider.
    
    The provider is selected via settings (LIBRARIAN_MODE/LLM_PROVIDER) and can route to
    API-hosted or open-source backends. The agent uses function calling (when supported)
    to query the TraceStore.
    
    The AI can:
    - List recent traces
    - Get detailed trace information
    - Search traces by keywords
    - Get tool usage statistics
    - Get database statistics
    """
    session_id = query.session_id or str(uuid.uuid4())

    if not LIBRARIAN_AVAILABLE:
        return NaturalLanguageResponse(
            answer="Librarian is not available. Please check LLM provider configuration and API keys.",
            session_id=session_id,
            suggestions=[],
            sources=None,
        )
    
    try:
        # Get librarian agent (lazy loading)
        agent = get_librarian_agent()
        
        # Query the agent
        result = agent.query(query.query, session_id=session_id)
        
        sources = result.get("sources")
        normalized_sources: Optional[List[str]] = None
        if sources is None:
            normalized_sources = None
        elif isinstance(sources, list):
            normalized_sources = []
            for item in sources:
                if isinstance(item, str):
                    normalized_sources.append(item)
                elif isinstance(item, dict):
                    value = item.get("id") or item.get("trace_id")
                    if value:
                        normalized_sources.append(str(value))
        else:
            normalized_sources = [str(sources)]

        return NaturalLanguageResponse(
            answer=result.get("answer", ""),
            session_id=session_id,
            suggestions=result.get("suggestions", []),
            sources=normalized_sources,
        )
        
    except Exception as e:
        logger.exception("Librarian query error")

        return NaturalLanguageResponse(
            answer=f"Sorry, I encountered an error processing your query: {str(e)}\n\nPlease try rephrasing your question or check the server logs.",
            session_id=session_id,
            suggestions=[],
            sources=[],
        )


@router.post("/ai_evaluate/{trace_id}", response_model=AIEvaluationOut, tags=["AI Evaluation"])
def evaluate_trace_with_ai(trace_id: str, payload: AIEvaluationIn):
    """
    Evaluate a trace with a judge model.
    
    This endpoint is designed as a hook for more complex AI evaluation logic.
    """
    try:
        judge = AIJudge(store)
        result = judge.evaluate(trace_id, payload.judge_model_id)

        confidence = float(result.get("confidence", 0.0))
        status_value = "auto_verified" if confidence > 0.8 else "pending_review"
        timestamp = datetime.utcnow().isoformat()
        ai_eval = {
            "rating": result.get("rating"),
            "feedback": result.get("feedback"),
            "confidence": confidence,
            "status": status_value,
            "timestamp": timestamp,
        }

        session = store.get_session()
        try:
            trace = session.query(Trace).filter(Trace.id == trace_id).first()
            if not trace:
                raise HTTPException(status_code=404, detail="Trace not found")
            trace.ai_evaluation = dict(ai_eval)
            session.commit()
        finally:
            session.close()

        return AIEvaluationOut(**ai_eval)

    except ValueError as e:
        message = str(e)
        if "Trace not found" in message:
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {e}")
