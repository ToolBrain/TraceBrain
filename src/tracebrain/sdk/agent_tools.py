"""
Agent tool wrappers for ToolBrain TraceStore.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import requests


def tool(func):
    """Lightweight decorator to mark a function as a tool."""
    func.is_tool = True
    return func


API_BASE_URL = os.getenv("TOOLBRAIN_API_BASE_URL", "http://localhost:8000/api/v1")


@tool
def search_past_experiences(task_description: str, min_rating: int = 4, limit: int = 3) -> Dict[str, Any]:
    """Find similar high-quality traces for in-context learning."""
    response = requests.get(
        f"{API_BASE_URL}/traces/search",
        params={"text": task_description, "min_rating": min_rating, "limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@tool
def search_similar_traces(query: str, min_rating: int = 4, limit: int = 3) -> Dict[str, Any]:
    """Find traces with semantically similar content."""
    response = requests.get(
        f"{API_BASE_URL}/traces/search",
        params={"text": query, "min_rating": min_rating, "limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@tool
def request_human_intervention(reason: str) -> Dict[str, Any]:
    """Escalate to the command center by flagging a trace for review."""
    trace_id = os.getenv("TOOLBRAIN_TRACE_ID")
    if not trace_id:
        return {
            "success": False,
            "message": "trace_id is required to signal a trace. Set TOOLBRAIN_TRACE_ID.",
            "reason": reason,
        }

    response = requests.post(
        f"{API_BASE_URL}/traces/{trace_id}/signal",
        json={"reason": reason},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
