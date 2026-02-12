"""
Curriculum curator for generating training tasks from failed traces.
"""

from __future__ import annotations

from typing import List, Dict, Any
import json
import logging
import re

from sqlalchemy import func, cast, Integer
from sqlalchemy.dialects.postgresql import JSONB

from tracebrain.core.llm_providers import select_provider, ProviderError
from tracebrain.db.base import Trace, CurriculumTask, TraceStatus

logger = logging.getLogger(__name__)


class CurriculumCurator:
    def __init__(self, store):
        self.store = store
        self.provider = None
        self.provider_error: str | None = None
        try:
            self.provider = select_provider()
        except ProviderError as exc:
            self.provider_error = str(exc)

    def find_failed_traces(self, limit: int = 20) -> List[Trace]:
        session = self.store.get_session()
        try:
            query = session.query(Trace)
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
                if (
                    (isinstance(rating, int) and rating < 3)
                    or trace.status == TraceStatus.failed
                    or str(trace.status).upper() == "ERROR"
                ):
                    results.append(trace)
            return results
        finally:
            session.close()

    def _summarize_traces(self, traces: List[Trace]) -> str:
        lines = []
        for trace in traces:
            reason = ""
            if trace.feedback and isinstance(trace.feedback, dict):
                reason = trace.feedback.get("comment") or ""
            status = trace.status.value if hasattr(trace.status, "value") else str(trace.status)
            lines.append(f"Trace {trace.id} | status={status} | feedback={reason}")
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

    def generate_curriculum(self) -> int:
        if not self.provider:
            raise ValueError(
                f"LLM provider not configured for curriculum generation: {self.provider_error}"
            )
        traces = self.find_failed_traces()
        if not traces:
            return 0

        summary = self._summarize_traces(traces)
        system_prompt = (
            "You analyze failed agent traces and propose training tasks. "
            "Return ONLY valid JSON as a list of objects with keys: task, reasoning, priority."
        )
        user_prompt = (
            "Analyze these failed agent traces. Identify 3 key weaknesses. "
            "Then, generate 5 specific, actionable training tasks (scenarios) to help the agent improve. "
            "Return the output as a JSON list of objects with keys: 'task', 'reasoning', 'priority'.\n\n"
            f"Failed Traces:\n{summary}"
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
