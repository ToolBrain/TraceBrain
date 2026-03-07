# my_agent_project/run_langchain_agent.py

import os
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import tool

from tracebrain import TraceClient

from converter import convert_langchain_to_otlp


@tool
def check_inventory(item: str) -> str:
    """Return a mock inventory status for an item."""
    inventory = {"laptop": "12 units", "monitor": "5 units", "keyboard": "24 units"}
    return inventory.get(item.lower(), "Out of stock")


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists() and not os.getenv("GOOGLE_API_KEY"):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except Exception:
            print("python-dotenv is not installed. Run: pip install python-dotenv")

    system_prompt = "You are a helpful inventory assistant. Use tools when needed."

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    agent = create_agent(model=model, tools=[check_inventory], system_prompt=system_prompt)

    client = TraceClient(base_url="http://localhost:8000")

    if not client.health_check():
        print("\nTraceBrain server is not running. Please start it first.")
        return

    user_message = "Check inventory for 'Laptop'"

    with client.trace_scope(system_prompt=system_prompt) as tracker:
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

        messages = result.get("messages", [])
        otlp_trace = convert_langchain_to_otlp(messages, system_prompt=system_prompt)
        tracker["spans"] = otlp_trace.get("spans", [])

    print("\nDone. Check the Trace Explorer UI.")


if __name__ == "__main__":
    main()
