"""AI judge logic for evaluating traces with prior episode context."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from tracebrain.core.llm_providers import ProviderError, select_provider

logger = logging.getLogger(__name__)


class AIJudge:
    """Evaluate traces using a judge LLM with prior episode feedback."""

    def __init__(self, store):
        self.store = store

    def _format_trace_summary(self, trace) -> str:
        """Create a concise summary of a trace for LLM consumption."""
        lines = [
            f"Trace ID: {trace.id}",
            f"System Prompt: {trace.system_prompt or 'N/A'}",
        ]

        for span in trace.spans or []:
            attrs = span.attributes or {}
            span_type = attrs.get("tracebrain.span.type", "unknown")
            thought = attrs.get("tracebrain.llm.thought")
            action = attrs.get("tracebrain.llm.tool_code")
            observation = attrs.get("tracebrain.tool.output")

            if isinstance(observation, (dict, list)):
                observation = json.dumps(observation)
            if observation:
                observation = str(observation)[:500]

            lines.append(
                "Span: "
                f"type={span_type}, "
                f"thought={thought or 'N/A'}, "
                f"action={action or 'N/A'}, "
                f"observation={observation or 'N/A'}"
            )

        return "\n".join(lines)

    def _get_prior_experience(self, episode_id: Optional[str], current_trace_id: str) -> str:
        """Gather human feedback from previous traces in the same episode."""
        if not episode_id:
            return ""

        traces = self.store.get_traces_by_episode_id(episode_id)
        examples = []
        for trace in traces:
            if trace.id == current_trace_id:
                continue
            if not trace.feedback:
                continue

            rating = trace.feedback.get("rating")
            comment = trace.feedback.get("comment") or trace.feedback.get("metadata")
            if rating is None:
                continue

            reason = comment if isinstance(comment, str) else json.dumps(comment) if comment else "No comment"
            examples.append(
                f"Trace {trace.id} was rated {rating} because {reason}."
            )

        if not examples:
            return ""

        return "\n".join(examples)

    def _extract_json(self, text: str) -> dict:
        """Parse a JSON object from model output, with fence cleanup."""
        if not text:
            raise ValueError("Empty response from judge model")

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def evaluate(self, trace_id: str, judge_model_id: str) -> dict:
        """Evaluate a trace using the judge model."""
        trace = self.store.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")

        prior = self._get_prior_experience(trace.episode_id, trace_id)
        summary = self._format_trace_summary(trace)

        system_instruction = (
            "You are an AI judge evaluating the quality of an agent trace. "
            "Return only strict JSON with keys: rating (0-5), feedback (string), "
            "and confidence (float between 0.0 and 1.0). "
            "If the trace shows clear success or obvious failure, confidence should be high. "
            "If the trace logic is ambiguous, circular, or lacks clear output, confidence should be lower."
        )
        user_content = (
            "Prior Experience (human-labeled examples):\n"
            f"{prior or 'None'}\n\n"
            "Current Trace Summary:\n"
            f"{summary}\n\n"
            "Guidelines:\n"
            "- rating: 0 (very poor) to 5 (excellent)\n"
            "- feedback: brief reasoning based on the trace and prior examples\n"
            "- confidence: 0.0 to 1.0 (higher when outcome is clear)\n"
            "Output JSON only."
        )
        prompt = f"{system_instruction}\n\n{user_content}"

        logger.debug("AIJudge prompt:\n%s", prompt)

        try:
            provider = select_provider(model_override=judge_model_id)
        except ProviderError as exc:
            raise ValueError(str(exc)) from exc

        response = provider.send_user_message(
            provider.start_chat(system_instruction, []),
            user_content,
        )
        raw_text = provider.extract_text(response)

        logger.debug("AIJudge raw response: %s", raw_text)

        parsed = self._extract_json(raw_text)
        rating = int(parsed.get("rating"))
        feedback = str(parsed.get("feedback", "")).strip()
        confidence = float(parsed.get("confidence"))

        if rating < 0 or rating > 5:
            raise ValueError("Judge rating out of range (0-5)")
        if not feedback:
            raise ValueError("Judge feedback is empty")
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("Judge confidence out of range (0.0-1.0)")

        return {"rating": rating, "feedback": feedback, "confidence": confidence}
