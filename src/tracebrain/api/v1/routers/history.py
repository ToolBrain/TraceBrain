"""
TraceBrain TraceStore REST API History Router (v1)

This router manages already viewed traces and episodes.

Features:
- GET /history: Retrieve paginated history of traces and episodes
- POST /history: Add or update a trace or episode in history
- DELETE /history: Clear all traces and episodes history
"""
from typing import Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from fastapi import status
from ..endpoints import TraceOut, _trace_to_out, store

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

# Pydantic Models
class HistoryListOut(BaseModel):
    type: str = Field(..., description="'trace' or 'episode'")
    data: Union[List[TraceOut], Dict[str, List[TraceOut]]] = Field(..., description="History data")
    has_more: bool = Field(..., description="Whether there are more items to load")
    total: int = Field(..., description="Total number of history entries")
    limit: int = Field(..., description="Number of items requested")
    offset: int = Field(..., description="Number of items skipped")


class HistoryAddRequest(BaseModel):
    id: str = Field(..., description="Trace or episode ID")
    type: str = Field(..., description="'trace' or 'episode'")


class HistoryResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    deleted_count: Optional[int] = Field(None, description="Number of entries deleted")

# API Endpoints
@router.get("", response_model=HistoryListOut, tags=["History"])
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
                    traces.append(_trace_to_out(trace))
            
            return HistoryListOut(
                type="trace",
                data=traces,
                has_more=has_more,
                total=total,
                limit=limit,
                offset=offset
            )
        
        elif type == "episode":
            result = {}
            episode_ids = [item.id for item in items]
            for episode_id in episode_ids:
                traces = store.get_traces_by_episode_id(episode_id)
                result[episode_id] = [_trace_to_out(trace) for trace in traces]
            
            return HistoryListOut(
                type="episode",
                data=result,
                has_more=has_more,
                total=total,
                limit=limit,
                offset=offset
            )
        
        else:
            raise HTTPException(status_code=400, detail="type parameter must be 'trace' or 'episode'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.post("", response_model=HistoryResponse, status_code=status.HTTP_201_CREATED, tags=["History"])
def add_history(request: HistoryAddRequest):
    """Record access to a trace or episode."""
    try:
        store.add_history(id=request.id, type=request.type)
        return HistoryResponse(success=True, message="History entry addeded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add history entry: {str(e)}")


@router.delete("", response_model=HistoryResponse, tags=["History"])
def clear_history():
    """Clear all history entries."""
    try:
        deleted_count = store.clear_history()
        return HistoryResponse(
            success=True,
            message="History cleared successfully",
            deleted_count=deleted_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")