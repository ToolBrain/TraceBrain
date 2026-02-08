"""Smolagent demo script that logs a trace to ToolBrain Tracing."""

import argparse
from datetime import datetime, timezone

from toolbrain_tracing import TraceClient


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_trace(trace_id: str):
    start = iso_now()
    end = iso_now()

    return {
        "trace_id": trace_id,
        "attributes": {
            "system_prompt": "You are a helpful assistant.",
            "toolbrain.episode.id": trace_id,
        },
        "spans": [
            {
                "span_id": "span_001",
                "parent_id": None,
                "name": "LLM Inference",
                "start_time": start,
                "end_time": end,
                "attributes": {
                    "toolbrain.span.type": "llm_inference",
                    "toolbrain.llm.thought": "I should use calculator for 2+2",
                    "toolbrain.llm.tool_code": "calculator({'expression': '2+2'})",
                },
            },
            {
                "span_id": "span_002",
                "parent_id": "span_001",
                "name": "Tool Execution",
                "start_time": start,
                "end_time": end,
                "attributes": {
                    "toolbrain.span.type": "tool_execution",
                    "toolbrain.tool.name": "calculator",
                    "toolbrain.tool.input": "{'expression': '2+2'}",
                    "toolbrain.tool.output": "4",
                },
            },
            {
                "span_id": "span_003",
                "parent_id": "span_001",
                "name": "LLM Final Answer",
                "start_time": start,
                "end_time": end,
                "attributes": {
                    "toolbrain.span.type": "llm_inference",
                    "toolbrain.llm.final_answer": "The answer is 4.",
                },
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Smolagent demo logger")
    parser.add_argument("--base-url", default="http://localhost:8000", help="ToolBrain API base URL")
    parser.add_argument("--trace-id", default="demo_trace_001", help="Trace ID")
    parser.add_argument("--api-key", default=None, help="Optional API key")
    args = parser.parse_args()

    client = TraceClient(base_url=args.base_url, api_key=args.api_key)
    trace = build_trace(args.trace_id)

    ok = client.log_trace(trace)
    if ok:
        print("Trace sent successfully")
    else:
        print("Failed to send trace")


if __name__ == "__main__":
    main()
