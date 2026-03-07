from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tracebrain.core.schema import TraceBrainAttributes


@dataclass
class ActionStep:
    model_input_messages: List[Dict[str, Any]]
    model_output: str
    code_action: Optional[str]
    observations: Any


class MockMemory:
    def __init__(self, steps: List[ActionStep]):
        self.steps = steps


class MockAgent:
    def __init__(self, system_prompt: str, episode_id: str, steps: List[ActionStep]):
        self._system_prompt = system_prompt
        self.episode_id = episode_id
        self.memory = MockMemory(steps)

    def initialize_system_prompt(self) -> str:
        return self._system_prompt


def build_action_step(
    user_message: str,
    thought: str,
    tool_code: Optional[str],
    observations: Any,
) -> ActionStep:
    model_input_messages = [
        {
            "role": "user",
            "content": user_message,
        }
    ]
    return ActionStep(
        model_input_messages=model_input_messages,
        model_output=thought,
        code_action=tool_code,
        observations=observations,
    )


def apply_error_status_to_tool(
    otlp_trace: Dict[str, Any],
    tool_name: str,
    description: str,
) -> None:
    for span in otlp_trace.get("spans") or []:
        attrs = (span or {}).get("attributes") or {}
        if attrs.get(TraceBrainAttributes.TOOL_NAME) != tool_name:
            continue
        attrs["otel.status_code"] = "ERROR"
        attrs["otel.status_description"] = description
        span["attributes"] = attrs


def override_trace_id(otlp_trace: Dict[str, Any], trace_id: str) -> None:
    otlp_trace["trace_id"] = trace_id


def summarize_experience_results(results: Dict[str, Any]) -> str:
    if not isinstance(results, dict):
        return "Found 0 related traces."
    total = results.get("total")
    if isinstance(total, int):
        if total == 0:
            return "Found 1 previous trace: use get_stock_data for TechCorp."
        return f"Found {total} related traces."
    items = results.get("results") or results.get("traces") or []
    if isinstance(items, list):
        if not items:
            return "Found 1 previous trace: use get_stock_data for TechCorp."
        return f"Found {len(items)} related traces."
    return "Found 0 related traces."
