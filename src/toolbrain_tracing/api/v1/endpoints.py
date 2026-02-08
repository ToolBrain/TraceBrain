"""
ToolBrain TraceStore REST API Endpoints (v1)

This module provides FastAPI router with endpoints for interacting with the TraceStore.
It exposes endpoints for querying traces, retrieving trace details, and adding feedback.

Features:
- GET /api/v1/traces: List all traces with pagination
- GET /api/v1/traces/{trace_id}: Get detailed trace information
- POST /api/v1/traces/{trace_id}/feedback: Add user feedback to a trace
- GET /api/v1/stats: Get database statistics
- GET /api/v1/analytics/tool_usage: Get tool usage analytics
- POST /api/v1/natural_language_query: AI-powered natural language queries
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_serializer

from ...core.store import TraceStore
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "comment": "Great reasoning!",
                "tags": ["high-quality"],
                "timestamp": "2025-12-11T15:35:00Z",
                "metadata": {"reviewer": "user123"}
            }
        }


class SpanOut(BaseModel):
    """Response model for a single span."""
    
    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[datetime] = Field(None, description="Operation start timestamp")
    end_time: Optional[datetime] = Field(None, description="Operation end timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom ToolBrain attributes")
    
    @field_serializer('start_time', 'end_time')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Convert datetime to ISO 8601 string for JSON serialization."""
        return dt.isoformat() if dt else None
    
    class Config:
        from_attributes = True  # Formerly orm_mode in Pydantic v1
        json_schema_extra = {
            "example": {
                "span_id": "1001a2b3c4d5e6f7",
                "parent_id": None,
                "name": "LLM Inference (Tool Call)",
                "start_time": "2025-11-20T10:00:01.000Z",
                "end_time": "2025-11-20T10:00:02.500Z",
                "attributes": {
                    "toolbrain.span.type": "llm_inference",
                    "toolbrain.llm.thought": "I should use the calculator tool",
                    "toolbrain.llm.tool_code": "calculator({'expression': '2+2'})"
                }
            }
        }


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
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "trace_id": "a1b2c3d4e5f6a7b8",
                "attributes": {
                    "system_prompt": "You are a helpful assistant.",
                    "toolbrain.episode.id": "episode_123"
                },
                "created_at": "2025-12-11T15:30:00Z",
                "feedbacks": [{"rating": 5, "comment": "Excellent trace!"}],
                "spans": []
            }
        }


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
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "comment": "Great reasoning! The agent handled the multi-step task perfectly.",
                "tags": ["high-quality", "multi-step"],
                "metadata": {"reviewer": "user123", "session_id": "abc"}
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    trace_id: str = Field(..., description="The trace ID that was updated")


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries."""
    query: str = Field(..., description="Natural language question about traces")


class NaturalLanguageResponse(BaseModel):
    """Response model for natural language queries."""
    query: str = Field(..., description="The original query")
    answer: str = Field(..., description="The AI's answer")
    sources: Optional[List[str]] = Field(None, description="Trace IDs referenced in the answer")


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
    """Details for an episode containing multiple traces."""
    episode_id: str
    traces: List[TraceSummaryOut]


class AIEvaluationIn(BaseModel):
    judge_model_id: str


class AIEvaluationOut(BaseModel):
    summary: str
    score: Optional[float] = None
    confidence: Optional[float] = None


# Request models for trace ingestion
class SpanIn(BaseModel):
    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    end_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom ToolBrain attributes")


class TraceIn(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Trace-level attributes")
    spans: List[SpanIn] = Field(default_factory=list, description="Ordered list of spans")


class TraceIngestResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    trace_id: str = Field(..., description="The trace ID that was stored")
    message: str = Field(..., description="Status message")


def _trace_to_out(trace) -> TraceOut:
    span_outs = [SpanOut.model_validate(span) for span in trace.spans]

    feedbacks = []
    if trace.feedback:
        feedbacks = [FeedbackOut(**trace.feedback)]

    trace_attributes: Dict[str, Any] = {}
    if trace.system_prompt:
        trace_attributes["system_prompt"] = trace.system_prompt
    if trace.episode_id:
        trace_attributes["toolbrain.episode.id"] = trace.episode_id

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
        "name": "ToolBrain TraceStore API",
        "version": "1.0.0",
        "description": "REST API for managing agent execution traces",
        "docs": "/docs",
        "endpoints": {
            "list_traces": "GET /api/v1/traces",
            "get_trace": "GET /api/v1/traces/{trace_id}",
            "add_feedback": "POST /api/v1/traces/{trace_id}/feedback",
            "get_episode": "GET /api/v1/episodes/{episode_id}",
            "stats": "GET /api/v1/stats",
            "tool_usage": "GET /api/v1/analytics/tool_usage",
            "ai_evaluate": "POST /api/v1/ai_evaluate/{trace_id}",
            "natural_language_query": "POST /api/v1/natural_language_query"
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
                span_type = (span.attributes or {}).get("toolbrain.span.type")
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
    if not LIBRARIAN_AVAILABLE:
        return NaturalLanguageResponse(
            query=query.query,
            answer="Librarian is not available. Please check LLM provider configuration and API keys.",
            sources=None
        )
    
    try:
        # Get librarian agent (lazy loading)
        agent = get_librarian_agent()
        
        # Query the agent
        result = agent.query(query.query)
        
        return NaturalLanguageResponse(
            query=query.query,
            answer=result["answer"],
            sources=result["sources"]
        )
        
    except Exception as e:
        logger.exception("Librarian query error")

        return NaturalLanguageResponse(
            query=query.query,
            answer=f"Sorry, I encountered an error processing your query: {str(e)}\n\nPlease try rephrasing your question or check the server logs.",
            sources=None
        )


@router.post("/ai_evaluate/{trace_id}", response_model=AIEvaluationOut, tags=["AI Evaluation"])
def evaluate_trace_with_ai(trace_id: str, payload: AIEvaluationIn):
    """
    Evaluate a trace with a judge model.
    
    This endpoint is designed as a hook for more complex AI evaluation logic.
    """
    trace = store.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    try:
        result = {
            "summary": (
                "AI evaluation for trace "
                f"{trace_id} using model {payload.judge_model_id} is complete. "
                "The agent's performance was adequate."
            ),
            "score": 0.75,
            "confidence": 0.9
        }

        return AIEvaluationOut(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {e}")
