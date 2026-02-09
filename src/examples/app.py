"""
ToolBrain 2.0 - Trace Management Platform WebUI

A Streamlit-based web application for visualizing and interacting with
agent execution traces stored in the TraceStore.

Features:
- 📊 Dashboard with key metrics and analytics
- 🔍 Trace Explorer for deep diving into individual traces
- 🤖 AI Librarian for natural language queries
- 💬 Feedback collection for human-in-the-loop labeling

Usage:
    streamlit run examples/app.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration

st.set_page_config(
    layout="wide",
    page_title="ToolBrain Trace Explorer",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("TOOLBRAIN_API_BASE_URL", "http://localhost:8000/api/v1")
_api_root = API_BASE_URL.rstrip("/")
if _api_root.endswith("/api/v1"):
    DOCS_URL = _api_root[:-7] + "/docs"
else:
    DOCS_URL = _api_root + "/docs"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .trace-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Helper Functions

def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def fetch_stats() -> Optional[Dict]:
    """Fetch statistics from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch stats: {e}")
        return None


def fetch_traces(limit: int = 20, skip: int = 0) -> Optional[Dict]:
    """Fetch traces from the API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/traces",
            params={"limit": limit, "skip": skip},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch traces: {e}")
        return None


def fetch_trace_details(trace_id: str) -> Optional[Dict]:
    """Fetch detailed information for a specific trace."""
    try:
        response = requests.get(f"{API_BASE_URL}/traces/{trace_id}", timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch trace details: {e}")
        return None


def fetch_tool_usage() -> Optional[Dict]:
    """Fetch tool usage analytics."""
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/tool_usage", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch tool usage: {e}")
        return None


def submit_feedback(trace_id: str, feedback_data: Dict) -> bool:
    """Submit feedback for a trace."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/traces/{trace_id}/feedback",
            json=feedback_data,
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to submit feedback: {e}")
        return False


def query_ai_librarian(query: str, session_id: Optional[str]) -> Optional[Dict]:
    """Send a natural language query to the AI Librarian."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/natural_language_query",
            json={"query": query, "session_id": session_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to query AI Librarian: {e}")
        return None


def fetch_librarian_history(session_id: str) -> Optional[Dict]:
    """Fetch persisted chat history for a Librarian session."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/librarian_sessions/{session_id}",
            timeout=10
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to load chat history: {e}")
        return None


def build_welcome_messages() -> List[Dict[str, str]]:
    return [
        {
            "role": "assistant",
            "content": "👋 Hello! I'm the ToolBrain AI Librarian. I'm powered by AI and can help you explore and analyze traces using real-time database queries.\n\n"
                       "**What I can do:**\n\n"
                       "• Show recent traces: *\"Show me the 5 most recent traces\"*\n"
                       "• Get trace details: *\"Get details for trace a1b2c3d4e5f6a7b8a1b2c3d4e5f6a7b8\"*\n"
                       "• Search by keyword: *\"Find all traces related to geography\"*\n"
                       "• Database statistics: *\"How many traces are in the database?\"*\n"
                       "• Tool usage analytics: *\"What tools are being used most?\"*\n\n"
                       "**Try asking me anything about the traces!** 🔍"
        }
    ]


def normalize_history_messages(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for item in history:
        role = item.get("role", "assistant")
        content = item.get("content", "")
        if role not in {"user", "assistant"}:
            role = "assistant"
            content = f"Tool log:\n```\n{content}\n```"
        messages.append({"role": role, "content": content})
    return messages


# Tab 1: Trace Dashboard

def render_dashboard():
    """Render the Trace Dashboard tab."""
    st.header("📊 Trace Dashboard")
    st.markdown("*Overview of all traces in the TraceStore*")
    st.divider()
    
    # Fetch statistics
    stats = fetch_stats()
    
    if stats:
        # Display KPI metrics
        st.subheader("📈 Key Metrics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Traces",
                value=stats.get("total_traces", 0),
                help="Total number of traces in the database"
            )
        
        with col2:
            st.metric(
                label="Total Spans",
                value=stats.get("total_spans", 0),
                help="Total number of spans across all traces"
            )
        
        with col3:
            st.metric(
                label="Avg Spans/Trace",
                value=stats.get("avg_spans_per_trace", 0),
                help="Average number of spans per trace"
            )
        
        with col4:
            st.metric(
                label="Last 24h",
                value=stats.get("traces_last_24h", 0),
                delta=f"+{stats.get('traces_last_24h', 0)}",
                help="Traces created in the last 24 hours"
            )
        
        with col5:
            st.metric(
                label="With Feedback",
                value=stats.get("traces_with_feedback", 0),
                help="Traces that have user feedback"
            )
        
        st.divider()
    
    # Display recent traces table
    st.subheader("📋 Recent Traces")
    
    data = fetch_traces(limit=20)
    
    if data and data.get("traces"):
        traces = data["traces"]
        
        # Convert to DataFrame for display
        df_data = []
        for trace in traces:
            # Extract system_prompt from nested attributes
            system_prompt = trace.get("attributes", {}).get("system_prompt", "")
            episode_id = trace.get("attributes", {}).get("toolbrain.episode.id", "")
            # Check if feedbacks list is not empty
            has_feedback = bool(trace.get("feedbacks"))
            
            df_data.append({
                "Trace ID": trace["trace_id"][:16] + "...",
                "Full ID": trace["trace_id"],  # Hidden column for copying
                "Episode ID": episode_id or "-",
                "Created": trace["created_at"][:19].replace("T", " "),
                "Spans": len(trace.get("spans", [])),
                "System Prompt": system_prompt[:60] + "..." if system_prompt else "No prompt",
                "Has Feedback": "✅" if has_feedback else "❌"
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with selection
        st.dataframe(
            df[["Trace ID", "Episode ID", "Created", "Spans", "System Prompt", "Has Feedback"]],
            use_container_width=True,
            hide_index=True
        )
        
        # Option to view full trace ID
        with st.expander("🔍 View Full Trace IDs"):
            for item in df_data:
                st.code(item["Full ID"], language=None)
    else:
        st.info("No traces found in the database. Run the seeding script to populate sample data.")
    
    st.divider()
    
    # Display tool usage analytics
    st.subheader("🔧 Tool Usage Analytics")
    
    tool_data = fetch_tool_usage()
    
    if tool_data and tool_data.get("tools"):
        tools = tool_data["tools"]
        
        # Create DataFrame for charting
        df_tools = pd.DataFrame(tools)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            st.bar_chart(
                df_tools.set_index("tool")["count"],
                use_container_width=True
            )
        
        with col2:
            # Summary table
            st.dataframe(
                df_tools,
                use_container_width=True,
                hide_index=True
            )
            
            st.metric(
                "Total Tool Calls",
                tool_data.get("total_tool_calls", 0)
            )
    else:
        st.info("No tool usage data available yet.")


# Tab 2: Trace Explorer

def render_trace_explorer():
    """Render the Trace Explorer tab."""
    st.header("🔍 Trace Explorer")
    st.markdown("*Deep dive into individual traces and provide feedback*")
    st.divider()
    
    # Trace ID input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        trace_id = st.text_input(
            "Enter Trace ID",
            placeholder="e.g., a1b2c3d4e5f6a7b8a1b2c3d4e5f6a7b8",
            help="Enter the full trace ID to explore"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Store trace_id in session state
    if search_button and trace_id:
        st.session_state["current_trace_id"] = trace_id
    
    # Display trace details if available
    if "current_trace_id" in st.session_state:
        trace_id = st.session_state["current_trace_id"]
        trace = fetch_trace_details(trace_id)
        
        if trace is None:
            st.error(f"❌ Trace with ID '{trace_id}' not found.")
            return
        
        st.success(f"✅ Loaded trace: `{trace_id}`")
        st.divider()
        
        # Trace metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Spans", len(trace.get("spans", [])))
        
        with col2:
            created_at = trace.get("created_at", "Unknown")
            st.metric("Created", created_at[:19].replace("T", " "))
        
        with col3:
            has_feedback = "Yes" if trace.get("feedbacks") else "No"
            st.metric("Has Feedback", has_feedback)

        with col4:
            episode_id = trace.get("attributes", {}).get("toolbrain.episode.id", "-")
            st.metric("Episode ID", episode_id)
        
        # System prompt
        st.subheader("💬 System Prompt")
        system_prompt = trace.get("attributes", {}).get("system_prompt", "No system prompt")
        st.text_area(
            "System Prompt",
            value=system_prompt,
            height=100,
            disabled=True,
            label_visibility="collapsed"
        )
        
        # Feedback (if exists)
        feedbacks = trace.get("feedbacks", [])
        if feedbacks:
            st.subheader("📝 Existing Feedback")
            for idx, feedback in enumerate(feedbacks, 1):
                with st.expander(f"Feedback #{idx}"):
                    st.json(feedback)
        
        st.divider()
        
        # Span tree visualization
        st.subheader("🌳 Span Hierarchy")
        
        spans = trace.get("spans", [])
        if spans:
            # Build parent-child map
            parent_map = {}
            for span in spans:
                parent_id = span.get("parent_id")
                if parent_id not in parent_map:
                    parent_map[parent_id] = []
                parent_map[parent_id].append(span)
            
            # Render tree starting from root (parent_id = None)
            def render_span_tree(parent_id: Optional[str], level: int = 0):
                """Recursively render span tree."""
                if parent_id not in parent_map:
                    return
                
                for span in parent_map[parent_id]:
                    span_id = span["span_id"]
                    name = span["name"]
                    attrs = span.get("attributes", {})
                    span_type = attrs.get("toolbrain.span.type", "unknown")
                    
                    # Create expander with indentation
                    indent = "　" * level  # Japanese space for visual indentation
                    icon = "🤖" if span_type == "llm_inference" else "🔧" if span_type == "tool_execution" else "📦"
                    
                    with st.expander(f"{indent}{icon} **{name}**", expanded=(level == 0)):
                        # Span metadata
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.text(f"Span ID: {span_id[:16]}...")
                            st.text(f"Type: {span_type}")
                        
                        with col2:
                            start = span.get("start_time")
                            end = span.get("end_time")
                            st.text(f"Start: {start[:19].replace('T', ' ') if start else 'N/A'}")
                            st.text(f"End: {end[:19].replace('T', ' ') if end else 'N/A'}")
                        
                        # Display key attributes based on type
                        if span_type == "llm_inference":
                            thought = attrs.get("toolbrain.llm.thought")
                            tool_code = attrs.get("toolbrain.llm.tool_code")
                            final_answer = attrs.get("toolbrain.llm.final_answer")
                            
                            if thought:
                                st.markdown("**💭 Thought:**")
                                st.info(thought)
                            
                            if tool_code:
                                st.markdown("**🔧 Tool Call:**")
                                st.code(tool_code, language="python")
                            
                            if final_answer:
                                st.markdown("**✅ Final Answer:**")
                                st.success(final_answer)
                        
                        elif span_type == "tool_execution":
                            tool_name = attrs.get("toolbrain.tool.name", "unknown")
                            tool_input = attrs.get("toolbrain.tool.input", "N/A")
                            tool_output = attrs.get("toolbrain.tool.output", "N/A")
                            
                            st.markdown(f"**🔧 Tool:** `{tool_name}`")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**📥 Input:**")
                                st.code(tool_input, language=None)
                            
                            with col2:
                                st.markdown("**📤 Output:**")
                                st.code(tool_output, language=None)
                            
                            # Check for errors
                            if attrs.get("otel.status_code") == "ERROR":
                                st.error(f"❌ Error: {attrs.get('otel.status_description', 'Unknown error')}")
                        
                        # Full attributes (collapsed)
                        with st.expander("🔍 View Full Attributes"):
                            st.json(attrs)
                        
                        # Recursively render children
                        render_span_tree(span_id, level + 1)
            
            # Start rendering from root spans
            render_span_tree(None, 0)
        else:
            st.info("No spans found in this trace.")
        
        st.divider()
        
        # Feedback form (sidebar)
        with st.sidebar:
            st.header("💬 Add Feedback")
            st.markdown(f"*For trace: `{trace_id[:16]}...`*")
            
            with st.form("feedback_form"):
                st.subheader("Rate this trace")
                
                outcome = st.radio(
                    "Overall Outcome",
                    options=["✅ Good", "❌ Bad", "⚠️ Partial"],
                    help="Was the agent's response correct and helpful?"
                )
                
                rating = st.slider(
                    "Quality Rating",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="Rate the overall quality (1=Poor, 5=Excellent)"
                )
                
                efficiency = st.slider(
                    "Efficiency Score",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How efficiently did the agent solve the task? (1=Many unnecessary steps, 5=Optimal)"
                )
                
                tags = st.multiselect(
                    "Tags",
                    options=[
                        "high-quality",
                        "low-quality",
                        "tool-error",
                        "reasoning-error",
                        "multi-step",
                        "simple",
                        "creative",
                        "needs-review"
                    ],
                    help="Select relevant tags"
                )
                
                comment = st.text_area(
                    "Comments",
                    placeholder="Optional: Add detailed feedback...",
                    help="Provide additional context or observations"
                )
                
                submit = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
                
                if submit:
                    feedback_data = {
                        "rating": rating,
                        "tags": tags,
                        "comment": comment if comment else None,
                        "metadata": {
                            "outcome": outcome,
                            "efficiency_score": efficiency
                        }
                    }
                    
                    if submit_feedback(trace_id, feedback_data):
                        st.success("✅ Feedback submitted successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to submit feedback. Please try again.")


# Tab 3: AI Librarian

def render_ai_librarian():
    """Render the AI Librarian tab."""
    st.header("🤖 AI Librarian")
    st.markdown("*Ask questions about traces in natural language*")
    st.divider()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = build_welcome_messages()

    if "librarian_session_id" not in st.session_state:
        st.session_state.librarian_session_id = None

    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    with st.container():
        col1, col2, col3 = st.columns([4, 1, 1])
        session_input = col1.text_input(
            "Session ID",
            value=st.session_state.librarian_session_id or "",
            placeholder="Paste a session id to restore history",
        )
        load_button = col2.button("Load Chat", use_container_width=True)
        new_button = col3.button("New Chat", use_container_width=True)

    if load_button:
        if session_input:
            history_payload = fetch_librarian_history(session_input)
            if history_payload and history_payload.get("messages"):
                st.session_state.messages = normalize_history_messages(history_payload["messages"])
                st.session_state.librarian_session_id = session_input
                st.session_state.pending_prompt = None
                st.success("✅ Restored chat history from the database.")
            else:
                st.warning("No history found for that session ID.")
        else:
            st.warning("Please enter a session ID to restore.")

    if new_button:
        st.session_state.messages = build_welcome_messages()
        st.session_state.librarian_session_id = None
        st.session_state.pending_prompt = None
        st.success("✅ Started a new chat.")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    prompt = st.session_state.pending_prompt or st.chat_input("Ask me about the traces...")
    if prompt:
        st.session_state.pending_prompt = None

        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Query the AI Librarian
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = query_ai_librarian(prompt, st.session_state.librarian_session_id)

                if response:
                    answer = response.get("answer", "I couldn't process that query.")
                    st.markdown(answer)

                    if response.get("session_id"):
                        st.session_state.librarian_session_id = response["session_id"]

                    suggestions = response.get("suggestions") or []
                    if suggestions:
                        st.markdown("**Suggestions**")
                        cols = st.columns(min(3, len(suggestions)))
                        for idx, suggestion in enumerate(suggestions):
                            label = suggestion.get("label") or "Suggestion"
                            value = suggestion.get("value")
                            col = cols[idx % len(cols)]
                            with col:
                                if st.button(label, key=f"suggestion-{idx}") and value:
                                    st.session_state.pending_prompt = value

                    # Display sources if available
                    if response.get("sources"):
                        with st.expander("📚 Sources"):
                            for source in response["sources"]:
                                st.code(source, language=None)
                else:
                    answer = "❌ Sorry, I encountered an error processing your query. Please try again."
                    st.markdown(answer)

                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": answer})


# Main Application

def main():
    """Main application entry point."""
    
    # Header
    st.markdown('<h1 class="main-header">🧠 ToolBrain 2.0 - Trace Management Platform</h1>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Cannot connect to the API server at " + API_BASE_URL)
        st.info(
            "Please start the API server first:\n\n"
            "```bash\n"
            "toolbrain-trace start\n"
            "```\n\n"
            "Or run via Docker:\n\n"
            "```bash\n"
            "toolbrain-trace up\n"
            "```"
        )
        st.stop()
    
    st.success("✅ Connected to TraceStore API")
    st.divider()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Trace Dashboard",
        "🔍 Trace Explorer",
        "🤖 AI Librarian (PoC)"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_trace_explorer()
    
    with tab3:
        render_ai_librarian()
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: gray; padding: 1rem;'>"
        "ToolBrain 2.0 - Open Source Framework for Training AI Agents | "
        f"<a href='{DOCS_URL}' target='_blank'>API Docs</a>"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
