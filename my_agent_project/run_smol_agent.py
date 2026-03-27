# my_agent_project/run_smol_agent.py

# --- User's own imports ---
from smolagents import CodeAgent, tool, TransformersModel

# --- TraceBrain import ---
from tracebrain import TraceClient
# from tracebrain.sdk.agent_tools import request_human_intervention, search_past_experiences

from converter import convert_smolagent_to_otlp

# PART 1: USER'S AGENT CODE 

@tool
def get_stock_price(ticker: str) -> float:
    """Gets the current stock price for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol, for example NVDA.
    """
    if ticker.upper() == "NVDA":
        return 125.50
    return 0.0

print("🚀 Initializing smolagent...")
my_model = TransformersModel(model_id="Qwen/Qwen2.5-3B-Instruct")
my_agent = CodeAgent(
    tools=[get_stock_price],
    model=my_model,
    instructions="You are a financial assistant. Focus on stock analysis. Use tools to answer questions."
)
print("✅ Agent is ready.")

# PART 2: RUN AND LOG TRACE TO TRACEBRAIN

if __name__ == "__main__":
    # 1. Initialize TraceClient
    client = TraceClient(base_url="http://localhost:8000")
    
    # 2. Check if the server is running
    if not client.health_check():
        print("\n❌ TraceBrain server is not running. Please run 'tracebrain up' first.")
    else:
        # 3. Run the agent inside trace_scope so tool calls attach to a trace_id.
        # This is required for Active Help Request and recommended for all runs.
        query = "What is the stock price of NVDA?"
        print(f"\n--- Running agent for query: '{query}' ---")
        with client.trace_scope(system_prompt=my_agent.instructions) as trace:
            my_agent.run(query)

            # 4. Convert results from agent's memory to OTLP and attach spans
            otlp_trace_data = convert_smolagent_to_otlp(my_agent, query)
            trace["spans"] = otlp_trace_data.get("spans", [])

        # 5. Check results on UI
        print("\n🎉 Process complete! Check the Trace Explorer UI.")