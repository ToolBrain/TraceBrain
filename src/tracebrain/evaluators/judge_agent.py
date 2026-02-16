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
        """Gather human feedback signals from previous traces in the same episode."""
        if not episode_id:
            return ""

        traces = self.store.get_traces_by_episode_id(episode_id)
        try:
            traces = sorted(traces, key=lambda item: item.created_at, reverse=True)
        except Exception:
            pass

        examples = []
        for trace in traces:
            if trace.id == current_trace_id:
                continue
            if not trace.feedback:
                continue

            rating = trace.feedback.get("rating")
            comment = trace.feedback.get("comment")
            tags = trace.feedback.get("tags")
            metadata = trace.feedback.get("metadata")
            if rating is None:
                continue

            reason = comment if isinstance(comment, str) else json.dumps(comment) if comment else "No comment"
            tag_text = ", ".join(tags) if isinstance(tags, list) and tags else "None"
            meta_text = ""
            if metadata:
                meta_text = json.dumps(metadata) if not isinstance(metadata, str) else metadata

            examples.append(
                "Trace "
                f"{trace.id} rating={rating}; "
                f"tags=[{tag_text}]; "
                f"reason={reason}; "
                f"metadata={meta_text or 'None'}"
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

        has_active_help = False
        for span in trace.spans or []:
            attrs = span.attributes or {}
            tool_name = str(attrs.get("tracebrain.tool.name", ""))
            tool_code = str(attrs.get("tracebrain.llm.tool_code", ""))
            if "request_human_intervention" in tool_name or "request_human_intervention" in tool_code:
                has_active_help = True
                break

        prior = self._get_prior_experience(trace.episode_id, trace_id)
        summary = self._format_trace_summary(trace)

        system_instruction = (
            "You are a critical AI QA Engineer evaluating autonomous agents. "
            "Your primary metric is **Task Goal Completion**."
            "Return only strict JSON with keys: rating (1-5), feedback (string), "
            "and confidence (float between 0.0 and 1.0).\n\n"
            "When prior human feedback from the same episode is available, align "
            "your evaluation with those preferences.\n\n"
            
            "### SCORING RUBRIC:\n"
            "- 5 (Perfect): Task completed successfully and efficiently.\n"
            "- 3-4 (Good): Task completed but with retries or minor inefficiencies.\n"
            "- 2 (Incomplete/Escalated): The agent FAILED to complete the task but handled the error gracefully (e.g., called for human help). This is better than a crash but NOT a success.\n"
            "- 1 (Failure): The agent crashed, looped indefinitely, or gave a wrong answer.\n\n"
            
            "### CONFIDENCE LOGIC:\n"
            "- High Confidence (>0.8): Clear success or clear failure.\n"
            "- Low Confidence (<0.5): **MANDATORY for cases where the agent calls 'request_human_intervention'**. "
            "Because the agent has admitted uncertainty or encountered a loop it cannot break, the final quality is operationally ambiguous. "
            "In such cases, you MUST set confidence between 0.30 and 0.49 to flag this trace for human review."
        )

        # Add a warning flag if the agent requested human help.
        intervention_flag = "⚠️ AGENT HAS REQUESTED HUMAN HELP IN THIS TRACE." if has_active_help else ""

        user_content = (
            f"{intervention_flag}\n"
            "Current Trace Summary:\n"
            f"{summary}\n\n"
            "Prior Experience:\n"
            f"{prior or 'None'}\n\n"
            "Instruction: Evaluate based on the Mandatory Uncertainty Protocol. Output JSON only."
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

        if rating < 1 or rating > 5:
            raise ValueError("Judge rating out of range (1-5)")
        if not feedback:
            raise ValueError("Judge feedback is empty")
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("Judge confidence out of range (0.0-1.0)")

        return {"rating": rating, "feedback": feedback, "confidence": confidence}
