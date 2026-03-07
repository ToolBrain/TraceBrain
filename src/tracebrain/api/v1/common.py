"""Shared dependencies and helpers for v1 routers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
import logging

from ...core.store import TraceStore
from ...evaluators.judge_agent import AIJudge
from ...core.librarian import LibrarianAgent
from ...config import settings

logger = logging.getLogger(__name__)

store = TraceStore(
    backend=settings.get_backend_type(),
    db_url=settings.DATABASE_URL,
)

_librarian_agent = None


def get_librarian_agent() -> LibrarianAgent:
    """Lazy initialization of Librarian agent."""
    global _librarian_agent
    if _librarian_agent is None:
        _librarian_agent = LibrarianAgent(store)
    return _librarian_agent


def build_ai_evaluation(result: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(result.get("confidence", 0.0))
    status_value = "auto_verified" if confidence > 0.8 else "pending_review"
    return {
        "rating": result.get("rating"),
        "feedback": result.get("feedback"),
        "confidence": confidence,
        "error_type": result.get("error_type", "none"),
        "status": status_value,
        "timestamp": datetime.utcnow().isoformat(),
    }


def run_bg_evaluation(trace_id: str) -> None:
    try:
        judge_model_id = settings.LLM_MODEL or "gemini-2.5-flash"
        judge = AIJudge(store)
        result = judge.evaluate(trace_id, judge_model_id)
        ai_eval = build_ai_evaluation(result)
        store.update_ai_evaluation(trace_id, ai_eval)
    except Exception as exc:
        logger.error("Background evaluation failed for %s: %s", trace_id, exc)
