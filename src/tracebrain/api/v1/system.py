"""System endpoints for v1."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...config import settings
from .common import store
from .schemas.api_models import (
    HistoryAddRequest,
    HistoryListOut,
    HistoryResponse,
    SettingsIn,
    SettingsOut,
    TraceOut,
    trace_to_out,
)

router = APIRouter()


@router.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
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
            "cleanup_traces": "DELETE /api/v1/ops/traces/cleanup",
            "init_trace": "POST /api/v1/traces/init",
            "add_feedback": "POST /api/v1/traces/{trace_id}/feedback",
            "signal_trace": "POST /api/v1/traces/{trace_id}/signal",
            "search_traces": "GET /api/v1/traces/search",
            "export_traces": "GET /api/v1/export/traces",
            "list_episodes": "GET /api/v1/episodes",
            "list_episode_summaries": "GET /api/v1/episodes/summary",
            "get_episode": "GET /api/v1/episodes/{episode_id}",
            "get_episode_traces": "GET /api/v1/episodes/{episode_id}/traces",
            "stats": "GET /api/v1/stats",
            "tool_usage": "GET /api/v1/analytics/tool_usage",
            "ai_evaluate": "POST /api/v1/ai_evaluate/{trace_id}",
            "natural_language_query": "POST /api/v1/natural_language_query",
            "librarian_session": "GET /api/v1/librarian_sessions/{session_id}",
            "curriculum_generate": "POST /api/v1/curriculum/generate",
            "curriculum_list": "GET /api/v1/curriculum",
            "curriculum_export": "GET /api/v1/curriculum/export",
            "get_history": "GET /api/v1/history",
            "add_history": "POST /api/v1/history",
            "clear_history": "DELETE /api/v1/history",
            "get_settings": "GET /api/v1/settings",
            "save_settings": "POST /api/v1/settings",
            "curriculum_delete_task": "DELETE /api/v1/curriculum/{task_id}",
            "curriculum_delete_all": "DELETE /api/v1/curriculum",
            "curriculum_complete_task": "PATCH /api/v1/curriculum/{task_id}/complete",
            "curriculum_complete_all": "PATCH /api/v1/curriculum/complete",
        },
    }


@router.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API and database connectivity."""
    try:
        store.list_traces(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "backend": settings.get_backend_type(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(exc)}")


@router.get("/settings", response_model=SettingsOut, tags=["Settings"])
async def get_settings() -> SettingsOut:
    """Load settings from the database."""
    try:
        return SettingsOut(**store.get_settings(mask_api_keys=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/settings", response_model=SettingsOut, tags=["Settings"])
async def save_settings(settings_payload: SettingsIn) -> SettingsOut:
    """Save provider/model settings to the database."""
    try:
        saved = store.save_settings(
            settings_payload.model_dump(exclude_unset=True),
            mask_api_keys=True,
        )
        return SettingsOut(**saved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history", response_model=HistoryListOut, tags=["History"])
def get_history(
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    type: str = Query(..., description="Filter by type 'trace' or 'episode'"),
    query: Optional[str] = Query(None, description="Filter by ID"),
):
    """Get paginated history of traces and episodes with full trace data."""
    try:
        items, total = store.get_history(limit=limit, offset=offset, type_filter=type, query=query)

        has_more = (offset + limit) < total

        if type == "trace":
            trace_ids = [item.id for item in items]
            traces = []
            for trace_id in trace_ids:
                trace = store.get_trace(trace_id)
                if trace:
                    traces.append(trace_to_out(trace))

            return HistoryListOut(
                type="trace",
                data=traces,
                has_more=has_more,
                total=total,
                limit=limit,
                offset=offset,
            )

        if type == "episode":
            result: Dict[str, Any] = {}
            episode_ids = [item.id for item in items]
            for episode_id in episode_ids:
                traces = store.get_traces_by_episode_id(episode_id)
                result[episode_id] = [trace_to_out(trace) for trace in traces]

            return HistoryListOut(
                type="episode",
                data=result,
                has_more=has_more,
                total=total,
                limit=limit,
                offset=offset,
            )

        raise HTTPException(status_code=400, detail="type parameter must be 'trace' or 'episode'")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(exc)}")


@router.post("/history", response_model=HistoryResponse, status_code=status.HTTP_201_CREATED, tags=["History"])
def add_history(request: HistoryAddRequest):
    """Record access to a trace or episode."""
    try:
        store.add_history(id=request.id, type=request.type)
        return HistoryResponse(success=True, message="History entry addeded successfully")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to add history entry: {str(exc)}")


@router.delete("/history", response_model=HistoryResponse, tags=["History"])
def clear_history():
    """Clear all history entries."""
    try:
        deleted_count = store.clear_history()
        return HistoryResponse(
            success=True,
            message="History cleared successfully",
            deleted_count=deleted_count,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(exc)}")
