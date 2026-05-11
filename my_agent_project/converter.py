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
    logged_messages_count = 0

    def _normalize_role(raw: str | None) -> str:
        if not raw:
            return "user"
        value = raw.lower()
        if "system" in value:
            return "system"
        if "assistant" in value or "ai" in value:
            return "assistant"
        if "tool" in value:
            return "tool"
        if "human" in value or "user" in value:
            return "user"
        return "user"

    def _extract_clean_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: List[str] = []
            for item in value:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item.get("text") or ""))
                else:
                    parts.append(_extract_clean_text(item))
            return "\n".join([p for p in parts if p])
        if isinstance(value, dict) and "text" in value:
            return str(value.get("text") or "")
        try:
            return json.dumps(value, ensure_ascii=True)
        except Exception:
            return str(value)

    def _stringify_content(value: Any) -> str:
        return _extract_clean_text(value)

    def _serialize_message(msg) -> Dict:
        role = None
        content = None

        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
        else:
            role = getattr(msg, "role", None)
            if role is None:
                role = getattr(msg, "type", None)
            content = getattr(msg, "content", None)
            if content is None and hasattr(msg, "model_dump"):
                dumped = msg.model_dump()
                role = role or dumped.get("role") or dumped.get("type")
                content = dumped.get("content")

        return {
            "role": _normalize_role(role),
            "content": _stringify_content(content),
        }

    def _to_iso(timestamp: float | datetime | None) -> str:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if isinstance(timestamp, datetime):
            return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def _to_timestamp(value: float | datetime | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).timestamp()
        return float(value)

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
        input_messages = list(step.model_input_messages or [])
        delta_messages = input_messages[logged_messages_count:]
        logged_messages_count = len(input_messages)
        new_content = [_serialize_message(msg) for msg in delta_messages]

        thought = step.model_output.strip()
        tool_code = step.code_action
        final_answer = None
        if tool_code and "final_answer" in tool_code:
            final_answer = _extract_final_answer(step.observations)
            if final_answer is None:
                final_answer = tool_code
            tool_code = None

        timing = step.timing
        start_time = getattr(timing, "start_time", None)
        end_time = getattr(timing, "end_time", None)
        duration = getattr(timing, "duration", None)
        if isinstance(duration, timedelta):
            duration = duration.total_seconds()

        start_ts = _to_timestamp(start_time)
        end_ts = _to_timestamp(end_time)
        if end_ts is None and start_ts is not None and duration is not None:
            end_ts = start_ts + float(duration)
        if start_ts is None and end_ts is not None and duration is not None:
            start_ts = end_ts - float(duration)

        usage = None
        if step.token_usage is not None:
            prompt_tokens = getattr(step.token_usage, "prompt_tokens", None)
            completion_tokens = getattr(step.token_usage, "completion_tokens", None)
            if prompt_tokens is None:
                prompt_tokens = getattr(step.token_usage, "input_tokens", None)
            if completion_tokens is None:
                completion_tokens = getattr(step.token_usage, "output_tokens", None)

            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": getattr(step.token_usage, "total_tokens", None),
            }
            if not any(isinstance(val, (int, float)) for val in usage.values()):
                usage = None

        llm_span = {
            "span_id": llm_span_id,
            "parent_id": parent_id,
            "name": "LLM Inference",
            "start_time": _to_iso(start_ts),
            "end_time": _to_iso(end_ts),
            "attributes": {
                TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                TraceBrainAttributes.LLM_NEW_CONTENT: json.dumps(new_content, ensure_ascii=True),
                TraceBrainAttributes.LLM_COMPLETION: _stringify_content(step.model_output),
                TraceBrainAttributes.LLM_THOUGHT: thought,
                TraceBrainAttributes.LLM_TOOL_CODE: tool_code,
                TraceBrainAttributes.LLM_FINAL_ANSWER: final_answer,
            },
        }
        if usage:
            llm_span["attributes"][TraceBrainAttributes.USAGE] = usage
        spans.append(llm_span)
        parent_id = llm_span_id

        if tool_code:
            tool_name = _extract_tool_name(tool_code)
            tool_span_id = uuid.uuid4().hex[:16]
            tool_start = end_ts if end_ts is not None else start_ts
            tool_end = tool_start
            tool_span = {
                "span_id": tool_span_id,
                "parent_id": parent_id,
                "name": f"Tool Execution: {tool_name}",
                "start_time": _to_iso(tool_start),
                "end_time": _to_iso(tool_end),
                "attributes": {
                    TraceBrainAttributes.SPAN_TYPE: SpanType.TOOL_EXECUTION,
                    TraceBrainAttributes.TOOL_NAME: tool_name,
                    TraceBrainAttributes.TOOL_INPUT: tool_code,
                    TraceBrainAttributes.TOOL_OUTPUT: _stringify_content(step.observations),
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

    def _extract_langchain_usage(msg: Any) -> Dict[str, Any] | None:
        usage = getattr(msg, "usage_metadata", None)
        if usage is None and isinstance(msg, dict):
            usage = msg.get("usage_metadata") or msg.get("usageMetadata")
        if not isinstance(usage, dict):
            return None

        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")
        if total_tokens is None and isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens

        usage_out: Dict[str, Any] = {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": total_tokens,
        }
        if "input_token_details" in usage:
            usage_out["input_tokens_details"] = usage.get("input_token_details")
        if "output_token_details" in usage:
            usage_out["output_tokens_details"] = usage.get("output_token_details")

        if not any(isinstance(val, (int, float)) for val in usage_out.values()):
            return None
        return usage_out


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
            usage = _extract_langchain_usage(msg)
            if usage:
                span["attributes"][TraceBrainAttributes.USAGE] = usage
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