"""Smolagent and LangChain to TraceBrain OTLP converter."""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from smolagents import CodeAgent

from tracebrain.core.schema import TraceBrainAttributes, SpanType, get_iso_time_now


def convert_smolagent_to_otlp(agent: CodeAgent, query: str) -> Dict:
    """
    Convert a smolagent's memory into a TraceBrain OTLP trace.
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
                TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                TraceBrainAttributes.LLM_NEW_CONTENT: json.dumps(new_content),
                TraceBrainAttributes.LLM_COMPLETION: step.model_output,
                TraceBrainAttributes.LLM_THOUGHT: thought,
                TraceBrainAttributes.LLM_TOOL_CODE: tool_code,
                TraceBrainAttributes.LLM_FINAL_ANSWER: final_answer,
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
                    TraceBrainAttributes.SPAN_TYPE: SpanType.TOOL_EXECUTION,
                    TraceBrainAttributes.TOOL_NAME: tool_name,
                    TraceBrainAttributes.TOOL_INPUT: tool_code,
                    TraceBrainAttributes.TOOL_OUTPUT: step.observations,
                },
            }
            spans.append(tool_span)
            parent_id = tool_span_id

    otlp_trace = {
        "trace_id": trace_id,
        "attributes": {
            TraceBrainAttributes.SYSTEM_PROMPT: agent.initialize_system_prompt(),
            TraceBrainAttributes.EPISODE_ID: episode_id,
        },
        "spans": spans,
    }

    print(f"Conversion complete. Created a trace with {len(spans)} spans.")
    return otlp_trace


def convert_langchain_to_otlp(messages: list, system_prompt: str = "") -> Dict:
    """
    Convert LangChain messages to a TraceBrain OTLP trace.
    """
    print("\n--- Converting LangChain messages to OTLP Trace ---")

    trace_id = uuid.uuid4().hex
    episode_id = f"ep-{uuid.uuid4().hex[:8]}"
    spans: List[Dict[str, Any]] = []
    parent_id: str | None = None

    tool_call_names: Dict[str, str] = {}
    tool_call_args: Dict[str, Any] = {}
    offset_ms = 0

    def _next_time() -> str:
        nonlocal offset_ms
        now = datetime.now(timezone.utc) + timedelta(milliseconds=offset_ms)
        offset_ms += 5
        return now.isoformat().replace("+00:00", "Z")

    def _serialize_message(role: str, content: Any, tool_calls: Any = None) -> str:
        payload: Dict[str, Any] = {"role": role, "content": content}
        if tool_calls:
            payload["tool_calls"] = tool_calls
        return json.dumps([payload], ensure_ascii=True)

    def _serialize_prev_message(prev_msg: Any) -> str:
        if not prev_msg:
            return json.dumps([], ensure_ascii=True)
        prev_type = getattr(prev_msg, "type", None) or prev_msg.__class__.__name__.lower()
        prev_role = "user" if "human" in prev_type else "assistant"
        prev_content = getattr(prev_msg, "content", "")
        return _serialize_message(prev_role, prev_content)

    def _format_tool_call(call: Dict[str, Any]) -> str:
        name = str(call.get("name") or "unknown")
        args = call.get("args") or {}
        try:
            args_text = json.dumps(args, ensure_ascii=True)
        except TypeError:
            args_text = json.dumps(str(args), ensure_ascii=True)
        return f"{name}({args_text})"

    prev_msg = None
    for msg in messages:
        msg_type = getattr(msg, "type", None) or msg.__class__.__name__.lower()
        content = getattr(msg, "content", "")

        if "human" in msg_type:
            span_id = uuid.uuid4().hex[:16]
            span = {
                "span_id": span_id,
                "parent_id": parent_id,
                "name": "LLM Inference",
                "start_time": _next_time(),
                "end_time": _next_time(),
                "attributes": {
                    TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                    TraceBrainAttributes.LLM_NEW_CONTENT: _serialize_message("user", content),
                },
            }
            spans.append(span)
            parent_id = span_id
            prev_msg = msg
            continue

        if "ai" in msg_type:
            tool_calls = getattr(msg, "tool_calls", None) or []
            tool_code = None
            thought = None
            final_answer = None

            if tool_calls:
                for call in tool_calls:
                    call_id = call.get("id")
                    call_name = call.get("name")
                    call_args = call.get("args")
                    if call_id and call_name:
                        tool_call_names[str(call_id)] = str(call_name)
                        tool_call_args[str(call_id)] = call_args
                tool_code = "; ".join(_format_tool_call(call) for call in tool_calls)
                thought = content or None
            else:
                final_answer = content

            span_id = uuid.uuid4().hex[:16]
            new_content = _serialize_prev_message(prev_msg)
            span = {
                "span_id": span_id,
                "parent_id": parent_id,
                "name": "LLM Inference",
                "start_time": _next_time(),
                "end_time": _next_time(),
                "attributes": {
                    TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                    TraceBrainAttributes.LLM_NEW_CONTENT: new_content,
                    TraceBrainAttributes.LLM_COMPLETION: content,
                    TraceBrainAttributes.LLM_THOUGHT: thought,
                    TraceBrainAttributes.LLM_TOOL_CODE: tool_code,
                    TraceBrainAttributes.LLM_FINAL_ANSWER: final_answer,
                },
            }
            spans.append(span)
            parent_id = span_id
            prev_msg = msg
            continue

        if "tool" in msg_type:
            tool_name = getattr(msg, "name", None)
            if not tool_name:
                call_id = getattr(msg, "tool_call_id", None)
                tool_name = tool_call_names.get(str(call_id), "unknown") if call_id else "unknown"
            tool_input = None
            call_id = getattr(msg, "tool_call_id", None)
            if call_id is not None:
                tool_input = tool_call_args.get(str(call_id))

            span_id = uuid.uuid4().hex[:16]
            span = {
                "span_id": span_id,
                "parent_id": parent_id,
                "name": f"Tool Execution: {tool_name}",
                "start_time": _next_time(),
                "end_time": _next_time(),
                "attributes": {
                    TraceBrainAttributes.SPAN_TYPE: SpanType.TOOL_EXECUTION,
                    TraceBrainAttributes.TOOL_NAME: tool_name,
                    TraceBrainAttributes.TOOL_INPUT: tool_input,
                    TraceBrainAttributes.TOOL_OUTPUT: content,
                },
            }
            spans.append(span)
            parent_id = span_id
            prev_msg = msg
            continue

    otlp_trace = {
        "trace_id": trace_id,
        "attributes": {
            TraceBrainAttributes.SYSTEM_PROMPT: system_prompt,
            TraceBrainAttributes.EPISODE_ID: episode_id,
        },
        "spans": spans,
    }

    print(f"Conversion complete. Created a trace with {len(spans)} spans.")
    return otlp_trace