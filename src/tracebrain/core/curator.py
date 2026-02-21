"""
Curriculum curator for generating training tasks from failed traces.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import json
import logging
import re

from sqlalchemy import func, cast, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import selectinload

from tracebrain.core.llm_providers import select_provider, ProviderError
from tracebrain.db.base import Trace, CurriculumTask, TraceStatus

logger = logging.getLogger(__name__)


class CurriculumCurator:
    VALID_ERROR_TYPES = {
        "logic_loop",
        "hallucination",
        "invalid_tool_usage",
        "tool_execution_error",
        "format_error",
        "misinterpretation",
        "context_overflow",
        "general_failure",
        "none",
    }

    def __init__(self, store):
        self.store = store
        self.provider = None
        self.provider_error: str | None = None
        try:
            self.provider = select_provider()
        except ProviderError as exc:
            self.provider_error = str(exc)

    def find_failed_traces(
        self,
        limit: int = 20,
        error_types: Optional[List[str]] = None,
    ) -> List[Trace]:
        normalized_error_types = self._normalize_error_types(error_types)
        session = self.store.get_session()
        try:
            query = session.query(Trace).options(selectinload(Trace.spans))
            if not self.store.is_sqlite:
                rating_value = cast(
                    func.jsonb_extract_path_text(cast(Trace.feedback, JSONB), "rating"),
                    Integer,
                )
                query = query.filter(
                    (rating_value < 3)
                    | (Trace.status == TraceStatus.failed)
                    | (Trace.status == "ERROR")
                )
                if normalized_error_types:
                    query = query.filter(
                        Trace.attributes["tracebrain.ai_evaluation"]["error_type"].astext.in_(
                            normalized_error_types
                        )
                    )
                return (
                    query.order_by(Trace.created_at.desc())
                    .limit(limit)
                    .all()
                )

            traces = (
                query.order_by(Trace.created_at.desc())
                .limit(limit)
                .all()
            )
            results: List[Trace] = []
            for trace in traces:
                rating = None
                if trace.feedback and isinstance(trace.feedback, dict):
                    rating = trace.feedback.get("rating")
                error_type = "general_failure"
                if isinstance(trace.attributes, dict):
                    ai_eval = trace.attributes.get("tracebrain.ai_evaluation") or {}
                    if isinstance(ai_eval, dict):
                        error_type = str(ai_eval.get("error_type") or "general_failure")
                if (
                    (isinstance(rating, int) and rating < 3)
                    or trace.status == TraceStatus.failed
                    or str(trace.status).upper() == "ERROR"
                ):
                    if normalized_error_types and error_type not in normalized_error_types:
                        continue
                    results.append(trace)
            return results
        finally:
            session.close()

    def _summarize_traces(self, traces: List[Trace]) -> str:
        lines = []
        for trace in traces:
            feedback_comment = ""
            if trace.feedback and isinstance(trace.feedback, dict):
                feedback_comment = trace.feedback.get("comment") or ""

            error_type = "general_failure"
            if isinstance(trace.attributes, dict):
                ai_eval = trace.attributes.get("tracebrain.ai_evaluation") or {}
                if isinstance(ai_eval, dict):
                    error_type = str(ai_eval.get("error_type") or "general_failure")

            error_details = []
            tool_usage = []

            recent_spans = (trace.spans or [])[-5:]
            for span in recent_spans:
                attrs = span.attributes or {}
                span_type = attrs.get("tracebrain.span.type")
                span_name = (span.name or "").lower()

                if span_type == "tool_execution" or "tool execution" in span_name:
                    tool_name = attrs.get("tracebrain.tool.name") or span.name
                    tool_output = str(attrs.get("tracebrain.tool.output", ""))[:200]
                    if tool_name:
                        tool_usage.append(f"Tool: {tool_name}")

                    lower_output = tool_output.lower()
                    error_markers = (
                        "error",
                        "exception",
                        "failed",
                        "failure",
                        "timeout",
                        "timed out",
                        "rate limit",
                        "unauthorized",
                        "forbidden",
                        "not found",
                        "invalid",
                        "traceback",
                        "stack trace",
                    )
                    has_error_marker = any(marker in lower_output for marker in error_markers)
                    has_status_code = re.search(r"\b[4-5]\d{2}\b", tool_output) is not None
                    if has_error_marker or has_status_code:
                        error_details.append(f"Tool Error: {tool_output}")

                if attrs.get("otel.status_code") == "ERROR":
                    desc = attrs.get("otel.status_description", "Unknown Error")
                    error_details.append(f"Span Error: {desc}")

            status = trace.status.value if hasattr(trace.status, "value") else str(trace.status)
            summary_line = (
                f"Trace ID: {trace.id[-6:]} | Status: {status} | Error Type: {error_type}"
            )
            if feedback_comment:
                summary_line += f" | Human Feedback: {feedback_comment}"
            if tool_usage:
                summary_line += f" | Actions: {', '.join(tool_usage)}"
            if error_details:
                summary_line += f" | ERRORS FOUND: {'; '.join(error_details)}"

            lines.append(summary_line)

        return "\n".join(lines)

    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        cleaned = (text or "").strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_error_types(
        self,
        error_types: Optional[List[str]],
    ) -> Optional[List[str]]:
        if not error_types:
            return None
        normalized = []
        for value in error_types:
            key = str(value).strip()
            if key in self.VALID_ERROR_TYPES:
                normalized.append(key)
        return normalized or None

    def generate_curriculum(
        self,
        error_types: Optional[List[str]] = None,
        limit: int = 5,
    ) -> int:
        if not self.provider:
            raise ValueError(
                f"LLM provider not configured for curriculum generation: {self.provider_error}"
            )
        normalized_error_types = self._normalize_error_types(error_types)
        traces = self.find_failed_traces(limit=limit, error_types=normalized_error_types)
        if not traces:
            return 0

        summary = self._summarize_traces(traces)
        system_prompt = (
            "You are an expert AI Coach for Autonomous Agents. Your goal is to design a training curriculum based on specific failure patterns. "
            "You must generate training tasks that directly address the specific error type found in the traces."
        )
        user_prompt = (
            "Generate tasks based on the following Error Type mapping:\n"
            "1. logic_loop: Task should force the agent to detect repetition and switch strategies or stop.\n"
            "2. hallucination: Task should require strict adherence to provided facts/tools (Grounding).\n"
            "3. invalid_tool_usage: Task should require complex tool calls with strict parameter schemas.\n"
            "4. tool_execution_error: Task should simulate API failures (500/429) to practice Error Handling & Backoff.\n"
            "5. format_error: Task should require generating complex valid JSON structures.\n"
            "6. misinterpretation: Task should require reading a complex tool output and reporting it 100% accurately.\n"
            "7. context_overflow: Task should require solving a problem in very few steps (Efficiency).\n\n"
            "If the error is 'general_failure' or 'none', generate general reasoning improvements.\n\n"
            "Analyze the following failed traces. Focus on the 'ERROR TYPE', 'ERRORS FOUND', and 'Human Feedback' sections.\n"
            f"Based on this, generate {limit} specific training scenarios (curriculum tasks) to teach the agent how to handle these situations better.\n"
            "The 'task' should be a prompt or scenario description.\n"
            "The 'reasoning' should explain why this helps the agent.\n\n"
            "Return valid JSON list of objects: [{'task': '...', 'reasoning': '...', 'priority': 'high/medium'}]\n"
            f"\n### FAILED TRACES LOG:\n{summary}"
        )

        session = self.provider.start_chat(system_prompt, [])
        response = self.provider.send_user_message(session, user_prompt)
        raw_text = self.provider.extract_text(response)

        tasks_payload = self._extract_json(raw_text)
        if not isinstance(tasks_payload, list):
            raise ValueError("Invalid curriculum output; expected a list")

        created = 0
        db_session = self.store.get_session()
        try:
            for item in tasks_payload:
                if not isinstance(item, dict):
                    continue
                task = str(item.get("task", "")).strip()
                reasoning = str(item.get("reasoning", "")).strip()
                priority = str(item.get("priority", "medium")).strip().lower() or "medium"
                if priority not in {"high", "medium", "low"}:
                    priority = "medium"
                if not task or not reasoning:
                    continue

                db_session.add(
                    CurriculumTask(
                        task_description=task,
                        reasoning=reasoning,
                        priority=priority,
                        status="pending",
                    )
                )
                created += 1
            db_session.commit()
            return created
        except Exception:
            db_session.rollback()
            logger.exception("Failed to save curriculum tasks")
            raise
        finally:
            db_session.close()
