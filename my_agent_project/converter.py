"""Smolagent to ToolBrain OTLP converter."""

import json
import re
import uuid
from typing import Dict

from smolagents import CodeAgent

from toolbrain_tracing.core.schema import ToolBrainAttributes, SpanType, get_iso_time_now


def convert_smolagent_to_otlp(agent: CodeAgent, query: str) -> Dict:
    """
    Convert a smolagent's memory into a ToolBrain OTLP trace.
    """
    print("\n--- Converting smolagent memory to OTLP Trace ---")

    trace_id = uuid.uuid4().hex
    episode_id = (
        getattr(agent, "episode_id", None)
        or getattr(agent, "session_id", None)
        or f"ep-{uuid.uuid4().hex[:8]}"
    )

    spans = []
    parent_id = None

    def _serialize_message(msg) -> Dict:
        if hasattr(msg, "model_dump"):
            return msg.model_dump()
        if hasattr(msg, "to_dict"):
            return msg.to_dict()
        if hasattr(msg, "dict"):
            return msg.dict()
        data = getattr(msg, "__dict__", {})
        if data:
            return data
        return {"content": str(msg)}

    def _extract_tool_name(code: str) -> str:
        if not code:
            return "unknown"
        for line in code.splitlines():
            candidate = line.strip()
            if not candidate:
                continue
            if "final_answer" in candidate:
                continue
            if "=" in candidate:
                candidate = candidate.split("=", 1)[1].strip()
            match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", candidate)
            if match:
                return match.group(1)
        fallback = code.split("(", 1)[0].strip()
        return fallback or "unknown"

    def _extract_final_answer(observations) -> str | None:
        if observations is None:
            return None
        if isinstance(observations, dict):
            for key in ("final_answer", "answer", "output", "result"):
                if key in observations and observations[key] is not None:
                    return str(observations[key])
            return json.dumps(observations)
        if isinstance(observations, list):
            for item in reversed(observations):
                if item:
                    return str(item)
            return None
        text = str(observations)
        last_output_match = re.search(
            r"Last output from code snippet:\s*(.+)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if last_output_match:
            last_output = last_output_match.group(1).strip()
            first_line = last_output.splitlines()[0].strip()
            return first_line or None
        marker = "Final answer:"
        if marker in text:
            return text.split(marker, 1)[1].strip()
        if "Execution logs:" in text:
            tail = text.split("Execution logs:", 1)[1].strip()
            first_line = tail.splitlines()[0].strip()
            return first_line or None
        return text.strip() or None

    for step in agent.memory.steps:
        if step.__class__.__name__ != "ActionStep":
            continue

        llm_span_id = uuid.uuid4().hex[:16]
        new_content = [_serialize_message(msg) for msg in step.model_input_messages]

        thought = step.model_output.strip()
        tool_code = step.code_action
        final_answer = None
        if tool_code and "final_answer" in tool_code:
            final_answer = _extract_final_answer(step.observations)
            if final_answer is None:
                final_answer = tool_code
            tool_code = None

        llm_span = {
            "span_id": llm_span_id,
            "parent_id": parent_id,
            "name": "LLM Inference",
            "start_time": get_iso_time_now(),
            "end_time": get_iso_time_now(),
            "attributes": {
                ToolBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                ToolBrainAttributes.LLM_NEW_CONTENT: json.dumps(new_content),
                ToolBrainAttributes.LLM_COMPLETION: step.model_output,
                ToolBrainAttributes.LLM_THOUGHT: thought,
                ToolBrainAttributes.LLM_TOOL_CODE: tool_code,
                ToolBrainAttributes.LLM_FINAL_ANSWER: final_answer,
            },
        }
        spans.append(llm_span)
        parent_id = llm_span_id

        if tool_code:
            tool_name = _extract_tool_name(tool_code)
            tool_span_id = uuid.uuid4().hex[:16]
            tool_span = {
                "span_id": tool_span_id,
                "parent_id": parent_id,
                "name": f"Tool Execution: {tool_name}",
                "start_time": get_iso_time_now(),
                "end_time": get_iso_time_now(),
                "attributes": {
                    ToolBrainAttributes.SPAN_TYPE: SpanType.TOOL_EXECUTION,
                    ToolBrainAttributes.TOOL_NAME: tool_name,
                    ToolBrainAttributes.TOOL_INPUT: tool_code,
                    ToolBrainAttributes.TOOL_OUTPUT: step.observations,
                },
            }
            spans.append(tool_span)
            parent_id = tool_span_id

    otlp_trace = {
        "trace_id": trace_id,
        "attributes": {
            ToolBrainAttributes.SYSTEM_PROMPT: agent.initialize_system_prompt(),
            ToolBrainAttributes.EPISODE_ID: episode_id,
        },
        "spans": spans,
    }

    print(f"Conversion complete. Created a trace with {len(spans)} spans.")
    return otlp_trace
