"""
TraceBrain Standard OTLP Trace Schema
-----------------------------------------
This module defines the semantic conventions and data structures for 
TraceBrain's tracing system. It implements the "Delta-based" architecture
where prompts are stored incrementally to save space.

Usage:
    Use the constants in TraceBrainAttributes to ensure consistency across
    parsers, adapters, and the TraceStore.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class TraceBrainAttributes(str, Enum):
    """
    Standard Attribute Keys for TraceBrain OTLP Spans.
    Use these constants instead of raw strings to avoid typos.
    """
    # --- Span Identity ---
    SPAN_TYPE = "tracebrain.span.type"
    
    # --- Trace Level Attributes (Top level) ---
    SYSTEM_PROMPT = "system_prompt"
    EPISODE_ID = "tracebrain.episode.id"
    AI_EVALUATION = "tracebrain.ai_evaluation"

    # --- LLM Inference Attributes ---
    # Stores only new messages in this turn (JSON string)
    LLM_NEW_CONTENT = "tracebrain.llm.new_content"
    # Raw completion from the model
    LLM_COMPLETION = "tracebrain.llm.completion"
    # Parsed semantic fields
    LLM_THOUGHT = "tracebrain.llm.thought"
    LLM_TOOL_CODE = "tracebrain.llm.tool_code"
    LLM_FINAL_ANSWER = "tracebrain.llm.final_answer"

    # --- Tool Execution Attributes ---
    TOOL_NAME = "tracebrain.tool.name"
    TOOL_INPUT = "tracebrain.tool.input"
    TOOL_OUTPUT = "tracebrain.tool.output"

    # --- AI Evaluation Sub-Fields ---
    AI_CONFIDENCE = "confidence"
    AI_RATING = "rating"
    AI_STATUS = "status"
    AI_FEEDBACK = "feedback"
    AI_ERROR_TYPE = "error_type"

class SpanType(str, Enum):
    """Allowed values for tracebrain.span.type"""
    LLM_INFERENCE = "llm_inference"
    TOOL_EXECUTION = "tool_execution"

# --- Pydantic Models for Validation ---

class Span(BaseModel):
    """
    Represents a single unit of work in the trace (OTLP Span).
    """
    span_id: str = Field(..., description="Unique 16-char hex identifier for the span")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root)")
    name: str = Field(..., description="Human readable name (e.g., 'LLM Inference')")
    start_time: str = Field(..., description="ISO 8601 UTC timestamp")
    end_time: str = Field(..., description="ISO 8601 UTC timestamp")
    
    # Attributes hold the semantic data (tracebrain.* fields)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "span_id": "00f067aa0ba902b7",
                "parent_id": None,
                "name": "LLM Inference (Tool Call)",
                "start_time": "2025-10-27T10:30:01.123456789Z",
                "end_time": "2025-10-27T10:30:02.234567890Z",
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.new_content": "[{\"role\": \"user\", \"content\": \"...\"}]",
                    "tracebrain.llm.completion": "..."
                }
            }
        }
    )

class Trace(BaseModel):
    """
    Represents a complete Agent Execution Trace.
    """
    trace_id: str = Field(..., description="Unique 32-char hex identifier for the trace")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Trace-level metadata (e.g., system_prompt)"
    )
    spans: List[Span] = Field(default_factory=list, description="Ordered list of spans")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                "attributes": {
                    "system_prompt": "You are a helpful assistant.",
                    "tracebrain.episode.id": "ep-123"
                },
                "spans": []
            }
        }
    )

# --- Helper Utilities ---

def get_iso_time_now() -> str:
    """Returns current time in ISO 8601 UTC format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')