"""Operations and analytics endpoints for v1."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ...config import settings
from ...evaluators.judge_agent import AIJudge
from .common import build_ai_evaluation, store

router = APIRouter()


@router.post("/ops/batch_evaluate", tags=["Operations"])
def batch_evaluate_traces(
    limit: int = Query(5, ge=1, le=50, description="Max traces to evaluate per call"),
):
    """Evaluate recent traces without AI evaluations and attach scores."""
    judge = AIJudge(store)
    processed = 0
    failed = 0
    errors: List[Dict[str, str]] = []
    TRACE_FETCH_LIMIT = 100
    try:
        traces = store.get_traces_by_start_time(TRACE_FETCH_LIMIT)
        filtered_traces = [t for t in traces if (t.attributes or {}).get("tracebrain.ai_evaluation") is None][:limit]
        for trace in filtered_traces:
            try:
                result = judge.evaluate(trace.id, settings.LLM_MODEL)
                ai_eval = build_ai_evaluation(result)
                store.update_ai_evaluation(trace.id, ai_eval)
                processed += 1
            except Exception as exc:
                failed += 1
                errors.append({"trace_id": trace.id, "error": str(exc)})

        message = (
            "No traces pending evaluation."
            if processed == 0
            else f"Successfully evaluated {processed} traces."
        )
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "message": message,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to batch evaluate traces: {str(exc)}")


@router.delete("/ops/traces/cleanup", tags=["Operations"])
def cleanup_traces(
    within_last_hours: Optional[int] = Query(
        None,
        ge=1,
        description="Delete traces older than this many hours",
    ),
    status: Optional[str] = Query(
        None,
        description="Delete traces by status (e.g., completed, failed, needs_review)",
    ),
):
    """Delete traces that match cleanup filters."""
    deleted = store.cleanup_traces(
        within_last_hours=within_last_hours,
        status=status,
    )
    timestamp = datetime.utcnow().isoformat()
    filters = {
        "within_last_hours": within_last_hours,
        "status": status,
    }
    return {
        "deleted": deleted,
        "filters": filters,
        "timestamp": timestamp,
    }


@router.get("/stats", tags=["Analytics"])
def get_stats():
    """
    Get overall statistics about the TraceStore.

    Returns:
        Dictionary with key metrics including total traces, spans, etc.
    """
    try:
        return store.get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(exc)}")


@router.get("/analytics/tool_usage", tags=["Analytics"])
def get_tool_usage(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of tools to return"),
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool usage: {str(exc)}")
