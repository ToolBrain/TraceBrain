"""AI-related endpoints for v1."""

from __future__ import annotations

from typing import Any, Dict, List
import uuid

from fastapi import APIRouter, HTTPException

from ...evaluators.judge_agent import AIJudge
from ...core.llm_providers import ProviderError
from .common import build_ai_evaluation, get_librarian_agent, store
from .schemas.api_models import (
    AIEvaluationIn,
    AIEvaluationOut,
    ChatHistoryOut,
    NaturalLanguageQuery,
    NaturalLanguageResponse,
)

router = APIRouter()


def _normalize_suggestions(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []

    normalized: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        suggestion_value = str(item.get("value", "")).strip()
        if label and suggestion_value:
            normalized.append({"label": label, "value": suggestion_value})
    return normalized


def _normalize_sources(value: Any) -> List[str]:
    normalized: List[str] = []

    def _append_candidate(candidate: Any) -> None:
        if candidate is None:
            return
        if isinstance(candidate, str):
            text = candidate.strip()
            if text:
                normalized.append(text)
            return
        if isinstance(candidate, dict):
            source_id = candidate.get("trace_id") or candidate.get("id")
            if source_id is not None:
                text = str(source_id).strip()
                if text:
                    normalized.append(text)
            return

        text = str(candidate).strip()
        if text:
            normalized.append(text)

    if isinstance(value, (list, tuple, set)):
        for item in value:
            _append_candidate(item)
    elif value is not None:
        _append_candidate(value)

    return list(dict.fromkeys(normalized))


def _normalize_filters(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(k).strip(): v for k, v in value.items() if k and v is not None}


def _build_nlq_response(result: Dict[str, Any], session_id: str) -> NaturalLanguageResponse:
    return NaturalLanguageResponse(
        answer=str(result.get("answer", "")),
        session_id=session_id,
        suggestions=_normalize_suggestions(result.get("suggestions")),
        sources=_normalize_sources(result.get("sources")),
        filters=_normalize_filters(result.get("filters")),
        is_error=bool(result.get("is_error", False)),
    )


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

    try:
        agent = get_librarian_agent()
        result = agent.query(query.query, session_id=session_id)
        if not isinstance(result, dict):
            result = {
                "answer": str(result),
                "suggestions": [],
                "sources": [],
                "filters": {},
            }
        return _build_nlq_response(result, session_id=session_id)

    except Exception as exc:
        if isinstance(exc, ProviderError):
            answer = str(exc)
        else:
            answer = (
                "Sorry, I encountered an error processing your query. "
                "Please try rephrasing your question or check the server logs."
            )
        return _build_nlq_response(
            {
                "answer": answer,
                "suggestions": [],
                "sources": [],
                "filters": {},
                "is_error": True,
            },
            session_id=session_id,
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
