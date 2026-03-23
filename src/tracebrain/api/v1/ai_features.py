"""AI-related endpoints for v1."""

from __future__ import annotations

from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException

from ...core.librarian import LIBRARIAN_AVAILABLE
from ...evaluators.judge_agent import AIJudge
from .common import build_ai_evaluation, get_librarian_agent, store
from .schemas.api_models import (
    AIEvaluationIn,
    AIEvaluationOut,
    ChatHistoryOut,
    NaturalLanguageQuery,
    NaturalLanguageResponse,
)

router = APIRouter()


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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(exc)}")


@router.post("/natural_language_query", response_model=NaturalLanguageResponse, tags=["AI"])
def natural_language_query(query: NaturalLanguageQuery):
    """
    Process a natural language query about traces using the configured LLM provider.

    The provider is selected via settings (LIBRARIAN_MODE/LLM_PROVIDER) and can route to
    API-hosted or open-source backends. The agent uses function calling (when supported)
    to query the TraceStore.
    """
    session_id = query.session_id or str(uuid.uuid4())

    if not LIBRARIAN_AVAILABLE:
        return NaturalLanguageResponse(
            answer="Librarian is not available. Please check LLM provider configuration and API keys.",
            session_id=session_id,
            suggestions=[],
            sources=[],
            filters={},
        )

    try:
        agent = get_librarian_agent()
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
            filters=result.get("filters", {}),
        )

    except Exception as exc:
        return NaturalLanguageResponse(
            answer=(
                "Sorry, I encountered an error processing your query: "
                f"{str(exc)}\n\nPlease try rephrasing your question or check the server logs."
            ),
            session_id=session_id,
            suggestions=[],
            sources=[],
            filters={},
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

        ai_eval = build_ai_evaluation(result)
        store.update_ai_evaluation(trace_id, ai_eval)

        return AIEvaluationOut(**ai_eval)

    except ValueError as exc:
        message = str(exc)
        if "Trace not found" in message:
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {exc}")
