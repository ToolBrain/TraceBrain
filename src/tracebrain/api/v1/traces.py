"""Trace endpoints for v1."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import Integer, cast, func
from sqlalchemy.dialects.postgresql import JSONB

from ...config import settings
from ...db.base import Trace, TraceStatus
from .common import run_bg_evaluation, store
from .schemas.api_models import (
    ExperienceSearchResponse,
    FeedbackIn,
    FeedbackResponse,
    TraceIn,
    TraceIngestResponse,
    TraceInitIn,
    TraceListOut,
    TraceOut,
    TraceSignalIn,
    trace_to_out,
)

router = APIRouter()


@router.get("/traces", response_model=TraceListOut, tags=["Traces"])
def list_traces(
    skip: int = Query(0, ge=0, description="Number of traces to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of traces to return"),
    query: Optional[str] = Query(None, description="Filter traces by ID"),
    status: Optional[str] = Query(
        None,
        description="Filter by trace status (e.g., 'completed', 'failed', 'needs_review')",
    ),
    min_rating: Optional[int] = Query(
        None,
        ge=1,
        le=5,
        description="Filter by minimum feedback rating",
    ),
    error_type: Optional[str] = Query(
        None,
        description="Filter by a specific error classification (e.g., 'logic_loop')",
    ),
    min_confidence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Filter by minimum AI evaluation confidence",
    ),
    max_confidence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Filter by maximum AI evaluation confidence",
    ),
    start_time: Optional[datetime] = Query(
        None,
        description="Filter traces created after this timestamp (ISO 8601)",
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="Filter traces created before this timestamp (ISO 8601)",
    ),
):
    """
    List all traces with pagination.

    Returns traces ordered by creation time (most recent first).
    """
    try:
        traces = store.list_traces(
            limit=limit,
            skip=skip,
            query=query,
            include_spans=True,
            status=status,
            min_rating=min_rating,
            error_type=error_type,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            start_time=start_time,
            end_time=end_time,
        )
        total = store.count_traces_filtered(
            query=query,
            status=status,
            min_rating=min_rating,
            error_type=error_type,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            start_time=start_time,
            end_time=end_time,
        )

        trace_outs = [trace_to_out(trace) for trace in traces]

        return TraceListOut(
            total=total,
            skip=skip,
            limit=limit,
            traces=trace_outs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {str(exc)}")


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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to search traces: {str(exc)}")


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
            raise HTTPException(status_code=404, detail=f"Trace with ID '{trace_id}' not found")

        return trace_to_out(trace)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace: {str(exc)}")


@router.post(
    "/traces",
    response_model=TraceIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Traces"],
)
def ingest_trace(trace: TraceIn, background_tasks: BackgroundTasks):
    """Ingest a trace into the TraceStore."""
    try:
        trace_payload = trace.model_dump()
        trace_id = store.add_trace_from_dict(trace_payload)
        attributes = trace_payload.get("attributes") or {}
        if not attributes.get("tracebrain.ai_evaluation"):
            background_tasks.add_task(run_bg_evaluation, trace_id)
        return TraceIngestResponse(
            success=True,
            trace_id=trace_id,
            message="Trace stored successfully",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to store trace: {str(exc)}")


@router.post(
    "/traces/init",
    response_model=TraceIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Traces"],
)
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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to initialize trace: {str(exc)}")


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
        feedback_data = feedback.model_dump(exclude_none=True)
        feedback_data["timestamp"] = datetime.utcnow().isoformat()
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
            trace_id=trace_id,
        )

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(exc)}")


@router.post("/traces/{trace_id}/signal", response_model=FeedbackResponse, tags=["Governance"])
def signal_trace_issue(trace_id: str, payload: TraceSignalIn):
    """Mark a trace as needing review based on an agent signal."""
    try:
        store.update_trace_status(trace_id, TraceStatus.needs_review)
        return FeedbackResponse(
            success=True,
            message="Trace flagged for review",
            trace_id=trace_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to signal trace: {str(exc)}")
