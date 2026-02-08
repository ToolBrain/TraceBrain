# my_agent_project/run_my_agent.py

# --- User's own imports ---
from smolagents import CodeAgent, tool, TransformersModel

# --- ToolBrain Tracing import ---
from toolbrain_tracing import TraceClient

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

# PART 2: RUN AND LOG TRACE TO TOOLBRAIN TRACING

if __name__ == "__main__":
    # 1. Initialize TraceClient
    client = TraceClient(base_url="http://localhost:8000")
    
    # 2. Check if the server is running
    if not client.health_check():
        print("\n❌ ToolBrain Tracing server is not running. Please run 'toolbrain-trace up' first.")
    else:
        # 3. Run the agent as usual
        query = "What is the stock price of NVDA?"
        print(f"\n--- Running agent for query: '{query}' ---")
        my_agent.run(query)

        # 4. Convert results from agent's memory to OTLP
        otlp_trace_data = convert_smolagent_to_otlp(my_agent, query)

        # 5. Send the converted trace to TraceStore
        print("\n--- Logging trace to TraceStore ---")
        client.log_trace(otlp_trace_data)

        # 6. Check results on UI
        print("\n🎉 Process complete! Check the Trace Explorer UI.")