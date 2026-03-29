"""Shared API models for v1 endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class FeedbackOut(BaseModel):
    """Response model for feedback data."""

    rating: Optional[int] = Field(None, description="Rating from 1-5")
    comment: Optional[str] = Field(None, description="Text comment or feedback")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    timestamp: Optional[str] = Field(None, description="When feedback was added")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "comment": "Great reasoning!",
                "tags": ["high-quality"],
                "timestamp": "2025-12-11T15:35:00Z",
                "metadata": {"reviewer": "user123"},
            }
        }
    )


class SpanOut(BaseModel):
    """Response model for a single span."""

    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[datetime] = Field(None, description="Operation start timestamp")
    end_time: Optional[datetime] = Field(None, description="Operation end timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom TraceBrain attributes")

    @field_serializer("start_time", "end_time")
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Convert datetime to ISO 8601 string for JSON serialization."""
        return dt.isoformat() if dt else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "span_id": "1001a2b3c4d5e6f7",
                "parent_id": None,
                "name": "LLM Inference (Tool Call)",
                "start_time": "2025-11-20T10:00:01.000Z",
                "end_time": "2025-11-20T10:00:02.500Z",
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.thought": "I should use the calculator tool",
                    "tracebrain.llm.tool_code": "calculator({'expression': '2+2'})",
                },
            }
        },
    )


class TraceOut(BaseModel):
    """Response model for a trace (OTLP Schema compliant)."""

    trace_id: str = Field(..., description="Unique trace identifier")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trace-level attributes including system_prompt and episode_id",
    )
    created_at: datetime = Field(..., description="Timestamp when trace was created")
    feedbacks: List[FeedbackOut] = Field(default_factory=list, description="List of user feedback on trace quality")
    spans: List[SpanOut] = Field(default_factory=list, description="List of spans in this trace")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "trace_id": "a1b2c3d4e5f6a7b8",
                "attributes": {
                    "system_prompt": "You are a helpful assistant.",
                    "tracebrain.episode.id": "episode_123",
                },
                "created_at": "2025-12-11T15:30:00Z",
                "feedbacks": [{"rating": 5, "comment": "Excellent trace!"}],
                "spans": [],
            }
        },
    )


class TraceListOut(BaseModel):
    """Response model for trace list with metadata."""

    total: int = Field(..., description="Total number of traces returned")
    skip: int = Field(..., description="Number of traces skipped")
    limit: int = Field(..., description="Maximum number of traces requested")
    traces: List[TraceOut] = Field(..., description="List of traces")


class FeedbackIn(BaseModel):
    """Request model for adding feedback to a trace."""

    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5")
    comment: Optional[str] = Field(None, description="Text comment or feedback")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    priority: Optional[int] = Field(None, description="The priority of the trace from 1-5")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "comment": "Great reasoning! The agent handled the multi-step task perfectly.",
                "tags": ["high-quality", "multi-step"],
                "metadata": {"reviewer": "user123", "session_id": "abc"},
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    trace_id: str = Field(..., description="The trace ID that was updated")


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries."""

    query: str = Field(..., description="Natural language question about traces")
    session_id: Optional[str] = Field(None, description="Conversation session ID")


class Suggestion(BaseModel):
    label: str
    value: str


class NaturalLanguageResponse(BaseModel):
    """Response model for natural language queries."""

    answer: str = Field(..., description="The AI's answer")
    session_id: str = Field(..., description="Conversation session ID")
    suggestions: Optional[List[Suggestion]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list, description="Trace IDs referenced in the answer")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filters extracted from the query")
    is_error: Optional[bool] = Field(False, description="Whether the response represents a provider error")


class ChatMessageOut(BaseModel):
    role: str
    content: Dict[str, Any]
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class ChatHistoryOut(BaseModel):
    session_id: str
    messages: List[ChatMessageOut]


class TraceSummaryOut(BaseModel):
    """Summary model for a trace inside an episode."""

    trace_id: str
    status: str
    duration_ms: float
    span_count: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class EpisodeOut(BaseModel):
    """Details for an episode containing multiple traces details."""

    episode_id: str
    traces: List[TraceSummaryOut]


class EpisodeTracesOut(BaseModel):
    """Details for an episode containing multiple traces."""

    episode_id: str
    traces: List[TraceOut]


class EpisodeAggregateOut(BaseModel):
    """Aggregated episode metrics."""

    episode_id: str
    start_time: datetime
    trace_count: int
    min_confidence: Optional[float] = None

    @field_serializer("start_time")
    def serialize_start_time(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class EpisodeListOut(BaseModel):
    """Response model for paginated episode list."""

    total: int
    skip: int
    limit: int
    episodes: List[EpisodeTracesOut]


class EpisodeSummaryListOut(BaseModel):
    """Response model for paginated episode summaries."""

    total: int
    skip: int
    limit: int
    episodes: List[EpisodeAggregateOut]


class AIEvaluationIn(BaseModel):
    judge_model_id: Optional[str] = None


class SettingsOut(BaseModel):
    """Response model for persistent provider/model and API key settings."""

    librarian_provider: str = Field(..., description="Librarian provider name")
    librarian_model: str = Field(..., description="Librarian model ID")
    judge_provider: str = Field(..., description="Judge provider name")
    judge_model: str = Field(..., description="Judge model ID")
    curator_provider: str = Field(..., description="Curator provider name")
    curator_model: str = Field(..., description="Curator model ID")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (masked on read)")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API key (masked on read)")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key (masked on read)")
    huggingface_api_key: Optional[str] = Field(None, description="Hugging Face API key (masked on read)")


class SettingsIn(BaseModel):
    """Request model for partial settings updates."""

    librarian_provider: Optional[str] = Field(None, description="Librarian provider name")
    librarian_model: Optional[str] = Field(None, description="Librarian model ID")
    judge_provider: Optional[str] = Field(None, description="Judge provider name")
    judge_model: Optional[str] = Field(None, description="Judge model ID")
    curator_provider: Optional[str] = Field(None, description="Curator provider name")
    curator_model: Optional[str] = Field(None, description="Curator model ID")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    huggingface_api_key: Optional[str] = Field(None, description="Hugging Face API key")


class SystemInfoOut(BaseModel):
    """Response model for lightweight runtime system metadata used by chat welcome UI."""

    database_type: str = Field(..., description="Active database type label (PostgreSQL or SQLite)")
    trace_count: int = Field(..., ge=0, description="Total number of traces indexed")
    model_name: str = Field(..., description="Current Librarian model name")


class AIEvaluationOut(BaseModel):
    rating: int = Field(..., ge=0, le=5, description="Rating from 0-5")
    feedback: str = Field(..., description="AI judge feedback")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Judge confidence score")
    error_type: Optional[str] = Field(None, description="Error classification label")
    status: Optional[str] = Field(None, description="Evaluation status")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority level (1-5)")
    timestamp: Optional[str] = Field(None, description="When the evaluation was recorded")


class TraceSignalIn(BaseModel):
    reason: str = Field(..., description="Issue description (looping, low confidence, etc.)")


class ExperienceSearchOut(BaseModel):
    trace_id: str
    score: Optional[float] = None
    rating: Optional[int] = None
    feedback: Optional[Dict[str, Any]] = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class ExperienceSearchResponse(BaseModel):
    total: int
    results: List[ExperienceSearchOut]


class CurriculumTaskOut(BaseModel):
    id: int
    task_description: str
    reasoning: str
    status: str
    priority: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        return dt.isoformat()


class GenerateCurriculumRequest(BaseModel):
    error_types: Optional[List[str]] = Field(
        default=None,
        description="Filter traces by specific error types (e.g., ['logic_loop', 'hallucination'])",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of tasks to generate",
    )


class SpanIn(BaseModel):
    span_id: str = Field(..., description="Unique span identifier")
    parent_id: Optional[str] = Field(None, description="Parent span ID (null for root spans)")
    name: str = Field(..., description="Human-readable operation name")
    start_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    end_time: Optional[str] = Field(None, description="ISO 8601 timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom TraceBrain attributes")


class TraceIn(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Trace-level attributes")
    spans: List[SpanIn] = Field(default_factory=list, description="Ordered list of spans")


class TraceIngestResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    trace_id: str = Field(..., description="The trace ID that was stored")
    message: str = Field(..., description="Status message")


class TraceInitIn(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    episode_id: Optional[str] = Field(None, description="Episode identifier")
    system_prompt: Optional[str] = Field(None, description="System prompt used by the agent")


class HistoryListOut(BaseModel):
    type: str = Field(..., description="'trace' or 'episode'")
    data: Union[List[TraceOut], Dict[str, List[TraceOut]]] = Field(
        ..., description="History data"
    )
    has_more: bool = Field(..., description="Whether there are more items to load")
    total: int = Field(..., description="Total number of history entries")
    limit: int = Field(..., description="Number of items requested")
    offset: int = Field(..., description="Number of items skipped")


class HistoryAddRequest(BaseModel):
    id: str = Field(..., description="Trace or episode ID")
    type: str = Field(..., description="'trace' or 'episode'")


class HistoryResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    deleted_count: Optional[int] = Field(None, description="Number of entries deleted")


def trace_to_out(trace) -> TraceOut:
    span_outs: List[SpanOut] = []
    for span in trace.spans:
        span_data = SpanOut.model_validate(span)
        if trace.system_prompt:
            span_data.attributes["system_prompt"] = trace.system_prompt
        span_outs.append(span_data)

    feedbacks: List[FeedbackOut] = []
    if trace.feedback:
        feedbacks = [FeedbackOut(**trace.feedback)]

    trace_attributes: Dict[str, Any] = {}
    if trace.system_prompt:
        trace_attributes["system_prompt"] = trace.system_prompt
    if trace.episode_id:
        trace_attributes["tracebrain.episode.id"] = trace.episode_id
    if trace.status:
        trace_attributes["tracebrain.trace.status"] = (
            trace.status.value if hasattr(trace.status, "value") else str(trace.status)
        )
    if trace.priority is not None:
        trace_attributes["tracebrain.trace.priority"] = trace.priority
    ai_eval = trace.ai_evaluation
    if not ai_eval and isinstance(trace.attributes, dict):
        ai_eval = trace.attributes.get("tracebrain.ai_evaluation")
    if ai_eval:
        trace_attributes["tracebrain.ai_evaluation"] = ai_eval

    return TraceOut(
        trace_id=trace.id,
        attributes=trace_attributes,
        created_at=trace.created_at,
        feedbacks=feedbacks,
        spans=span_outs,
    )
