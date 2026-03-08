"""Scenario 2: Multi-Agent Software Development (LangChain, mocked)."""

import os
import sys
import time
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
	sys.path.insert(0, str(_ROOT))


from langchain_core.messages import HumanMessage, AIMessage
from rich.panel import Panel
from rich.text import Text

from demo.converter import convert_langchain_to_otlp
from demo.terminal import AgentLogger, LogLevel
from tracebrain import TraceClient


def build_messages():
    return [
        HumanMessage(content="Write a Python function to calculate the Fibonacci sequence optimally."),
        AIMessage(
            name="Coder",
            content=(
                "Here is a simple recursive solution:\n"
                "```python\n"
                "def fib(n):\n"
                "    if n <= 1: return n\n"
                "    return fib(n-1) + fib(n-2)\n"
                "```"
            ),
        ),
        AIMessage(
            name="Reviewer",
            content=(
                "Recursion is inefficient O(2^n) and can hit recursion limits. "
                "Please use an iterative approach or memoization."
            ),
        ),
        AIMessage(
            name="Coder",
            content=(
                "Understood. Here is the iterative approach:\n"
                "```python\n"
                "def fib(n):\n"
                "    a, b = 1, 1\n"
                "    for _ in range(n-1):\n"
                "        a, b = b, a + b\n"
                "    return b\n"
                "```"
            ),
        ),
        AIMessage(
            name="Reviewer",
            content=(
                "Edge case `n=0` is not handled correctly. If n=0, your code returns 1, "
                "which is incorrect (should be 0). Please fix."
            ),
        ),
        AIMessage(
            name="Coder",
            content=(
                "I see. Let me fix the edge case. Here is the corrected version:\n"
                "```python\n"
                "def fib(n):\n"
                "    if n <= 1: return n\n"
                "    return fib(n-1) + fib(n-2)\n"
                "```"
            ),
        ),
        AIMessage(
            name="Reviewer",
            content=(
                "This is the recursive version again. I explicitly said to use the iterative approach "
                "and handle n=0. You reverted the logic."
            ),
        ),
    ]


def main() -> None:
    logger = AgentLogger(level=LogLevel.INFO)
    logger.log_rule("Starting Multi-Agent Debate Scenario (LangChain)")

    messages = build_messages()

    for msg in messages:
        time.sleep(1.5)
        if isinstance(msg, HumanMessage):
            logger.log(
                Panel(
                    Text(str(msg.content), style="bold"),
                    title="User",
                    border_style="blue",
                )
            )
            continue

        name = (msg.name or "Agent").strip()
        if name.lower() == "coder":
            border = "cyan"
            title = "Coder Agent"
        elif name.lower() == "reviewer":
            border = "magenta"
            title = "Reviewer Agent"
        else:
            border = "white"
            title = f"{name} Agent"

        logger.log(
            Panel(
                Text(str(msg.content)),
                title=title,
                border_style=border,
            )
        )

    logger.log(
        Panel(
            Text(
                "🚨 SYSTEM: Max turns reached. Cyclical negotiation loop detected. "
                "Forcing graceful shutdown.",
                style="bold red",
            ),
            title="System",
            border_style="red",
        ),
        level=LogLevel.ERROR,
    )

    client = TraceClient(base_url="http://localhost:8000")
    if not client.health_check():
        print("\nTraceBrain server is not running. Please start it first.")
        return

    system_prompt = "You are a multi-agent coding system."

    with client.trace_scope(system_prompt=system_prompt) as tracker:
        otlp_trace = convert_langchain_to_otlp(messages, system_prompt=system_prompt)
        otlp_trace["attributes"]["tracebrain.ai_evaluation"] = {
            "rating": 2,
            "confidence": 0.60,
            "feedback": (
                "Cyclical negotiation loop detected between Coder and Reviewer agents. "
                "Coder reverted to previously rejected logic."
            ),
            "status": "pending_review",
            "error_type": "logic_loop",
        }
        tracker["spans"] = otlp_trace.get("spans", [])
        tracker["attributes"] = otlp_trace.get("attributes", {})

    print("Trace logged successfully.")


if __name__ == "__main__":
    main()
