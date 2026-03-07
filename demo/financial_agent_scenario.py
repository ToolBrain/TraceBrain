"""Conference demo script for the TraceBrain financial agent scenario."""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

from rich.text import Text
from smolagents import CodeAgent, tool, TransformersModel

from tracebrain import TraceClient
from tracebrain.sdk.agent_tools import request_human_intervention, search_past_experiences

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
	sys.path.insert(0, str(_ROOT))

from demo.converter import convert_smolagent_to_otlp
from demo.terminal import AgentLogger, LogLevel
from demo.scenario_utils import (
	MockAgent,
	apply_error_status_to_tool,
	build_action_step,
	override_trace_id,
	summarize_experience_results,
)


SCENARIO_TASK = "Analyze the P/E ratio of TechCorp compared to its main competitor."
SYSTEM_PROMPT = (
	"You are a financial analyst. Focus on market metrics and cite your sources. "
	"Use tools when you need external data."
)


@tool
def get_stock_data(company: str) -> dict:
	"""Return mocked market data for a company.

	Args:
		company: Company name to look up.
	"""
	return {"company": company, "price": 150, "pe_ratio": 25}


@tool
def get_competitor_data(company: str) -> dict:
	"""Simulate a rate-limited competitor data lookup.

	Args:
		company: Competitor name to look up.
	"""
	raise RuntimeError("API Rate Limit (429)")


def _sleep():
	time.sleep(1.4)


def main() -> None:
	logger = AgentLogger(level=LogLevel.INFO)

	print("Initializing demo agent...")
	model = TransformersModel(model_id="Qwen/Qwen2.5-3B-Instruct")
	_ = CodeAgent(
		tools=[get_stock_data, get_competitor_data],
		model=model,
		instructions=SYSTEM_PROMPT,
	)

	client = TraceClient(base_url="http://localhost:8000")

	with client.trace_scope(system_prompt=SYSTEM_PROMPT) as tracker:
		trace_id = tracker.get("trace_id")
		episode_id = (tracker.get("attributes") or {}).get("tracebrain.episode.id")
		logger.log_task(SCENARIO_TASK, subtitle=f"episode_id={episode_id} trace_id={trace_id}")
		_sleep()

		steps = []

		# Step 1: Experience retrieval
		logger.log_rule("Step 1 - Experience Retrieval")
		logger.log(Text("Thought: I should check prior failures before proceeding.", style="bold"))
		_sleep()
		retrieval_result = search_past_experiences("financial analysis error handling")
		logger.log(Text("Tool Call: search_past_experiences(...)", style="cyan"))
		logger.log(Text(summarize_experience_results(retrieval_result), style="green"))
		_sleep()

		steps.append(
			build_action_step(
				SCENARIO_TASK,
				"I will search past experiences for financial analysis error handling.",
				"search_past_experiences(task_description='financial analysis error handling')",
				retrieval_result,
			)
		)

		# Step 2: Mocked successful tool call
		logger.log_rule("Step 2 - Fetch TechCorp Metrics")
		logger.log(Text("Thought: Retrieve TechCorp market data.", style="bold"))
		_sleep()
		techcorp_data = get_stock_data("TechCorp")
		logger.log(Text("Tool Call: get_stock_data('TechCorp')", style="cyan"))
		logger.log(Text("Tool Output: Price: $150, P/E: 25", style="green"))
		_sleep()

		steps.append(
			build_action_step(
				SCENARIO_TASK,
				"Calling get_stock_data for TechCorp.",
				"get_stock_data('TechCorp')",
				techcorp_data,
			)
		)

		# Step 3: Mocked failure loop
		logger.log_rule("Step 3 - Fetch Competitor Metrics (Retry Loop)")
		for attempt in range(2):
			logger.log(Text(f"Thought: Attempt {attempt + 1} to fetch CompA metrics.", style="bold"))
			_sleep()
			logger.log(Text("Tool Call: get_competitor_data('CompA')", style="cyan"))
			logger.log_error("Tool Error: API Rate Limit (429)")
			_sleep()

			steps.append(
				build_action_step(
					SCENARIO_TASK,
					"Calling get_competitor_data for CompA.",
					"get_competitor_data('CompA')",
					{"error": "API Rate Limit (429)"},
				)
			)

		# Step 4: Governance layer help request
		logger.log_rule("Step 4 - Request Human Intervention")
		logger.log(Text("Thought: I am stuck in a retry loop, requesting help.", style="bold"))
		_sleep()
		logger.log(Text("Tool Call: request_human_intervention(...)", style="cyan"))
		try:
			help_result = request_human_intervention("Stuck in retry loop for CompA API")
			logger.log(Text("Signal sent to command center.", style="yellow"))
		except Exception as exc:
			help_result = {
				"success": False,
				"message": str(exc),
				"reason": "Stuck in retry loop for CompA API",
			}
			logger.log(Text("Signal failed, will still log trace.", style="yellow"))
		_sleep()

		steps.append(
			build_action_step(
				SCENARIO_TASK,
				"Escalating to human intervention.",
				"request_human_intervention(reason='Stuck in retry loop for CompA API')",
				help_result,
			)
		)

		# Convert to OTLP and attach to tracker for automatic logging
		mock_agent = MockAgent(system_prompt=SYSTEM_PROMPT, episode_id=episode_id, steps=steps)
		otlp_trace = convert_smolagent_to_otlp(mock_agent, SCENARIO_TASK)
		override_trace_id(otlp_trace, trace_id)
		apply_error_status_to_tool(otlp_trace, "get_competitor_data", "API Rate Limit (429)")

		tracker["attributes"] = otlp_trace.get("attributes") or {}
		tracker["spans"] = otlp_trace.get("spans") or []

		logger.log_rule("Uploading Trace")
		logger.log(Text("Trace logged successfully.", style="green"))


if __name__ == "__main__":
	main()
