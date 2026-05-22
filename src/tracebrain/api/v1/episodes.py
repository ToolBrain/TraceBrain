"""Episode endpoints for v1."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .common import store
from .schemas.api_models import (
    EpisodeAggregateOut,
    EpisodeListOut,
    EpisodeOut,
    EpisodeSummaryListOut,
    EpisodeTracesOut,
    TraceSummaryOut,
    trace_to_out,
)

router = APIRouter(prefix="/episodes", tags=["Episodes"])


@router.get("", response_model=EpisodeListOut)
def list_episodes(
    skip: int = Query(0, ge=0, description="Number of episodes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of episodes to return"),
    query: Optional[str] = Query(None, description="Filter episodes by ID"),
    min_confidence_lt: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Filter episodes where minimum confidence is below this value",
    ),
):
    """List all episodes ordered by creation time, each with their traces."""
    try:
        episodes, total = store.list_episodes(
            skip=skip,
            limit=limit,
            query=query,
            include_spans=True,
            min_confidence_lt=min_confidence_lt,
        )

        episode_outs = []
        for episode_id, traces in episodes:
            trace_outs = [trace_to_out(trace) for trace in traces]
            episode_outs.append(EpisodeTracesOut(episode_id=episode_id, traces=trace_outs))

        return EpisodeListOut(total=total, skip=skip, limit=limit, episodes=episode_outs)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list episodes: {str(exc)}")

@router.delete("/{episode_id}")
def delete_episode(episode_id: str):
    """Delete an episode and all its traces."""
    try:
        store.delete_episode(episode_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete episode: {str(exc)}")

@router.get("/summary", response_model=EpisodeSummaryListOut)
def list_episode_summaries(
    skip: int = Query(0, ge=0, description="Number of episodes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of episodes to return"),
    query: Optional[str] = Query(None, description="Filter episodes by ID"),
    min_confidence_lt: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Filter episodes where minimum confidence is below this value",
    ),
):
    """List episodes with aggregated metrics."""
    try:
        episodes, total = store.list_episode_summaries(
            skip=skip,
            limit=limit,
            query=query,
            min_confidence_lt=min_confidence_lt,
        )

        episode_outs = [EpisodeAggregateOut(**episode) for episode in episodes]

        return EpisodeSummaryListOut(total=total, skip=skip, limit=limit, episodes=episode_outs)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list episode summaries: {str(exc)}")


@router.get("/{episode_id}", response_model=EpisodeOut)
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
                    created_at=trace.created_at,
                )
            )

        return EpisodeOut(episode_id=episode_id, traces=trace_summaries)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{episode_id}/traces", response_model=EpisodeTracesOut)
def get_episode_traces(episode_id: str):
    """Get all traces related to an episode."""
    try:
        traces_in_episode = store.get_traces_by_episode_id(episode_id)
        if not traces_in_episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        trace_ids = [trace.id for trace in traces_in_episode]
        traces = store.get_traces_by_ids(trace_ids, include_spans=True)
        trace_outs = [trace_to_out(trace) for trace in traces]
        return EpisodeTracesOut(episode_id=episode_id, traces=trace_outs)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
