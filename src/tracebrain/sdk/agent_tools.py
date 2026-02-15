"""
Agent tool wrappers for TraceBrain TraceStore.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import requests


def tool(func):
    """Lightweight decorator to mark a function as a tool."""
    func.is_tool = True
    return func


API_BASE_URL = os.getenv("TRACEBRAIN_API_BASE_URL", "http://localhost:8000/api/v1")


class ActiveHelpRequest(RuntimeError):
    """Raised when an agent explicitly requests human intervention."""

    def __init__(self, reason: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(reason)
        self.reason = reason
        self.response = response or {}


def _init_trace_if_missing(trace_id: str) -> None:
    if not trace_id:
        return
    try:
        requests.post(
            f"{API_BASE_URL}/traces/init",
            json={"trace_id": trace_id},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        return


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
    trace_id = os.getenv("TRACEBRAIN_TRACE_ID")
    if not trace_id:
        return {
            "success": False,
            "message": "trace_id is required to signal a trace. Set TRACEBRAIN_TRACE_ID.",
            "reason": reason,
        }

    response = requests.post(
        f"{API_BASE_URL}/traces/{trace_id}/signal",
        json={"reason": reason},
        timeout=10,
    )
    if response.status_code == 404:
        _init_trace_if_missing(trace_id)
        response = requests.post(
            f"{API_BASE_URL}/traces/{trace_id}/signal",
            json={"reason": reason},
            timeout=10,
        )
    response.raise_for_status()
    return response.json()


@tool
def request_human_intervention_and_abort(reason: str) -> Dict[str, Any]:
    """Escalate to the command center and abort execution.

    Args:
        reason: Short description of why human intervention is needed.
    """
    try:
        response = request_human_intervention(reason)
    except Exception as exc:
        response = {
            "success": False,
            "message": str(exc),
            "reason": reason,
        }
    raise ActiveHelpRequest(reason=reason, response=response)
