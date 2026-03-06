"""
Librarian AI Agent for TraceBrain TraceStore Natural Language Queries

This module provides a provider-agnostic text-to-SQL agent with conversational
memory, self-correction, and interactive abstention.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import re

import sqlparse

from tracebrain.config import settings
from tracebrain.core.llm_providers import select_provider, is_provider_available, BaseProvider
from tracebrain.core.schema import TraceBrainAttributes

logger = logging.getLogger(__name__)


def _build_tool_specs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "run_sql_query",
            "description": "Execute a read-only SQL SELECT query against the TraceStore database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute",
                    }
                },
                "required": ["query"],
            },
        }
        ,
        {
            "name": "search_similar_traces",
            "description": "Find semantically similar traces using vector search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query describing the target behavior or failure",
                    },
                    "min_rating": {
                        "type": "integer",
                        "description": "Minimum human feedback rating to include (use higher to focus on best traces)",
                        "default": 4,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (keep small for focused context)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "set_api_filters",
            "description": (
                "Call this ALWAYS after a data-fetching tool returns results, whenever the query conditions map to the available fields. "
                "This registers the active filter state. "
                "Only skip this if a condition cannot be represented by the available fields. "
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Execution status of the trace"
                    },
                    "min_rating": {
                        "type": "integer", 
                        "minimum": 1, 
                        "maximum": 5,
                        "description": "Minimum human feedback rating to include"
                    },
                    "error_type": {
                        "type": "string",
                        "description": "Category of error encountered during agent execution",
                    },
                    "min_confidence": {
                        "type": "number", 
                        "minimum": 0.0, 
                        "maximum": 1.0,
                        "description": "Lower bound AI confidence score from trace evaluation"
                    },
                    "max_confidence": {
                        "type": "number", 
                        "minimum": 0.0, 
                        "maximum": 1.0,
                        "description": "Upper bound AI confidence score from trace evaluation"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Filter traces that started at or after this ISO 8601 timestamp (e.g. '2020-01-01T00:00:00Z')",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Filter traces that started at or before this ISO 8601 timestamp (e.g. '2025-01-01T23:59:59Z')",
                    },
                },
                "additionalProperties": False,
            },
        },
    ]

def _validate_filters(filters: dict) -> dict | None:
    if not filters:
        return None
    if not all(key in {"status", "min_rating", "error_type", "min_confidence", "max_confidence", "start_time", "end_time"} for key in filters):
        return None
    return filters

LIBRARIAN_AVAILABLE = is_provider_available()


class LibrarianAgent:
    """Text-to-SQL agent with conversational memory and self-correction."""

    def __init__(self, store):
        self.store = store
        self.tools = _build_tool_specs()

    def _schema_context(self) -> str:
        ai_eval_key = TraceBrainAttributes.AI_EVALUATION.value
        ai_conf = TraceBrainAttributes.AI_CONFIDENCE.value
        ai_rating = TraceBrainAttributes.AI_RATING.value
        ai_status = TraceBrainAttributes.AI_STATUS.value
        ai_feedback = TraceBrainAttributes.AI_FEEDBACK.value
        span_type = TraceBrainAttributes.SPAN_TYPE.value
        tool_name = TraceBrainAttributes.TOOL_NAME.value

        dialect = self._detect_dialect()

        if dialect == "sqlite":
            json_examples = (
                "JSON usage examples (SQLite json_extract):\n"
                f"- json_extract(spans.attributes, '$.\"{ span_type}\"')\n"
                f"- json_extract(spans.attributes, '$.\"{tool_name}\"')\n"
                "- json_extract(spans.attributes, '$.\"otel.status_code\"')\n"
                "- json_extract(traces.feedback, '$.\"rating\"')\n"
                f"- json_extract(traces.attributes, '$.\"{ai_eval_key}\".{ai_conf}')\n\n"
                "Advanced SQL examples:\n"
                f"- Uncertainty query: SELECT id FROM traces WHERE CAST(json_extract(attributes, '$.\"{ai_eval_key}\".{ai_conf}') AS REAL) < 0.5\n"
                f"- Feedback search: SELECT id FROM traces WHERE json_extract(attributes, '$.\"{ai_eval_key}\".{ai_feedback}') LIKE '%loop%'\n"
                "- Time filter: created_at > datetime('now', '-24 hours')\n"
                "- Metadata join: spans.trace_id = traces.id\n"
            )
        else:
            json_examples = (
                "JSONB usage examples (use ->> for text comparisons):\n"
                f"- spans.attributes->>'{span_type}'\n"
                f"- spans.attributes->>'{tool_name}'\n"
                "- spans.attributes->>'otel.status_code'\n"
                "- traces.feedback->>'rating'\n"
                f"- traces.attributes->'{ai_eval_key}'->>'{ai_conf}'\n\n"
                "Advanced SQL examples:\n"
                f"- Uncertainty query: SELECT id FROM traces WHERE (attributes->'{ai_eval_key}'->>'{ai_conf}')::float < 0.5\n"
                f"- Feedback search: SELECT id FROM traces WHERE attributes->'{ai_eval_key}'->>'{ai_feedback}' ILIKE '%loop%'\n"
                "- Time filter: created_at > now() - interval '24 hours'\n"
                "- Metadata join: spans.trace_id = traces.id\n"
            )

        return (
            f"{dialect.upper()} schema (read-only):\n\n"
            "Table: traces\n"
            "- id (string, primary key)\n"
            "- system_prompt (text)\n"
            "- episode_id (string)\n"
            "- created_at (timestamp)\n"
            "- feedback (jsonb)\n"
            "- attributes (jsonb)\n\n"
            "Table: spans\n"
            "- id (integer, primary key)\n"
            "- span_id (string)\n"
            "- trace_id (string, foreign key -> traces.id)\n"
            "- parent_id (string)\n"
            "- name (string)\n"
            "- start_time (timestamp)\n"
            "- end_time (timestamp)\n"
            "- attributes (jsonb)\n\n"
            "AI Evaluation object:\n"
            f"- traces.attributes contains '{ai_eval_key}' (JSON object)\n"
            f"  - '{ai_rating}': integer (1-5)\n"
            f"  - '{ai_conf}': float (0.0-1.0). High uncertainty is < 0.5\n"
            f"  - '{ai_status}': string (pending_review, auto_verified, completed)\n"
            f"  - '{ai_feedback}': string (AI rationale)\n\n"
            f"{json_examples}"
        ).strip()

    def _system_prompt(self) -> str:
        dialect = self._detect_dialect()

        if dialect == "sqlite":
            sql_rules = (
                "### CRITICAL SQL RULES:\n"
                "- Database is SQLite.\n"
                "- For type casting use CAST(x AS REAL).\n"
                "- For time filters use datetime('now', '-6 months').\n"
                "- For JSON fields use json_extract(column, '$.key').\n"
                "- To see agent thoughts or tool outputs, you MUST JOIN 'traces' and 'spans' on 'spans.trace_id = traces.id'.\n"
                "- Only perform SELECT queries. If the database returns EMPTY_RESULT, do not guess; explain that no data matches the criteria.\n\n"
            )
        else:
            sql_rules = (
                "### CRITICAL SQL RULES:\n"
                "- All timestamps are in UTC. Use 'now() - interval X hours' for relative time queries.\n"
                "- To see agent thoughts or tool outputs, you MUST JOIN 'traces' and 'spans' on 'spans.trace_id = traces.id'.\n"
                "- For JSONB fields, use '->>' to get values as text (e.g., attributes->>'tracebrain.tool.name').\n"
                "- Only perform SELECT queries. If the database returns EMPTY_RESULT, do not guess; explain that no data matches the criteria.\n\n"
            )

        return (
            "You are the TraceBrain AI Librarian, an expert in Agent Operations (AgentOps). "
            "Your task is to analyze agent execution traces to help human experts diagnose issues.\n\n"
            "NEVER show raw SQL queries or technical tool outputs to the end-user in the 'answer' field. "
            "If the user gives no time range, assume all time and proceed immediately without asking for clarification until you truly struggle to get any results.\n"
            "Your final response MUST ALWAYS be a valid JSON object with 'answer', 'suggestions', 'sources' and 'filters' keys. "
            "The 'answer' should be a natural language summary of what you found in the database.\n\n"
            
            "### CORE TOOLS:\n"
            "1. run_sql_query: Use this for counts, status filters, time-based queries, and metadata analysis.\n"
            "2. search_similar_traces: Use this ONLY when the user asks for 'similar' cases or semantic patterns in reasoning/thoughts.\n\n"
            "3. set_api_filters: Always call this after fetching data if the query conditions map to its available fields, to register the active filter state.\n\n"
            
            f"{sql_rules}"
            
            "### OUTPUT FORMAT (Strict JSON):\n"
            "{"
            "\"answer\": \"A concise summary of findings. Mention specific errors or patterns found.\", "
            "\"suggestions\": [{\"label\": \"Follow-up question\", \"value\": \"Exact query text\"}], "
            "\"sources\": [\"list of trace_ids discovered\"],"
            "\"filters\": \"the filter conditions applied in the SQL query if used - only include this key if ALL filters in the user's query map to these exact keys: status, min_rating, start_time, end_time, error_type, min_confidence, max_confidence. If any filter criteria falls outside these keys, omit the filters key entirely. "
            "Example: {\\\"status\\\": \\\"completed\\\", \\\"min_rating\\\": 4, \\\"start_time\\\": \\\"2022-01-01T00:00:00Z\\\", \\\"end_time\\\": \\\"2026-01-02T00:00:00Z\\\", \\\"error_type\\\": \\\"logic_loop\\\", \\\"min_confidence\\\": 0.4, \\\"max_confidence\\\": 0.9}\""
            "}\n\n"
            f"{self._schema_context()}"
        )

    def _detect_dialect(self) -> str:
        return self.store.engine.dialect.name

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "None"
        lines = []
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty response from LLM")

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _extract_sources(self, answer: str) -> Optional[List[str]]:
        potential_ids = re.findall(r"[a-f0-9]{32}", answer)
        return list(set(potential_ids)) if potential_ids else None

    def run_sql_query(self, sql_query: str) -> str:
        """Executes a READ-ONLY SQL query on the TraceStore."""
        response = self.store.execute_read_only_sql(sql_query)

        if "error" in response:
            return f"EXECUTION_FAILED: {response['error']}"

        if response.get("count", 0) == 0:
            return "EMPTY_RESULT: No data found for this query."

        return json.dumps(response.get("rows", []), default=str)

    def _abstain_response(self) -> Dict[str, Any]:
        return {
            "answer": "I could not find any matching data. Can you clarify what you want to explore next?",
            "suggestions": [
                {"label": "Widen time range", "value": "Try the last 30 days"},
                {"label": "Search by episode", "value": "Filter by tracebrain.episode.id"},
                {"label": "Search by tool", "value": "Filter by tracebrain.tool.name"},
            ],
            "sources": [],
            "filters": {},
        }

    def _abstain_response_from_llm(self, user_query: str, history_text: str, provider: BaseProvider) -> Dict[str, Any]:
        system_prompt = (
            "You are the TraceBrain AI Librarian expert. The database returned EMPTY_RESULT for the user's request.\n\n"
            "### YOUR TASK:\n"
            "1. Analyze the User Question and explain politely that no traces currently match those specific criteria.\n"
            "2. Identify potential reasons for the empty result (e.g., a time range that is too narrow, a specific error code that hasn't occurred, or a tool name typo).\n"
            "3. Provide 3-4 ACTIONABLE suggestions to help the user find what they need. These should be formatted as direct questions or commands the user can click.\n\n"
            "### SUGGESTION GUIDELINES:\n"
            "- 'Broaden Time': Suggest looking back further (e.g., last 7 days).\n"
            "- 'Relax Filters': If they asked for errors, suggest looking for all traces of that tool.\n"
            "- 'Semantic Search': Suggest using natural language to find 'similar behavior' instead of exact SQL matches.\n\n"
            "### OUTPUT RULES:\n"
            "Return ONLY a strict JSON object:\n"
            "{\n"
            "  \"answer\": \"A professional explanation of why no data was found and what might be the cause.\",\n"
            "  \"suggestions\": [\n"
            "    {\"label\": \"Short label for UI button\", \"value\": \"The full natural language query to try next\"}\n"
            "  ],\n"
            "  \"sources\": []\n"
            "}"
        )
        user_content = (
            "Conversation History:\n"
            f"{history_text}\n\n"
            "User Question:\n"
            f"{user_query}\n\n"
            "Return JSON only."
        )
        try:
            session = provider.start_chat(system_prompt, [])
            response = provider.send_user_message(session, user_content)
            answer_text = provider.extract_text(response)
            parsed = self._extract_json(answer_text)

            answer = str(parsed.get("answer", "")).strip()
            suggestions = self._normalize_suggestions(parsed.get("suggestions"))
            if not answer:
                raise ValueError("Empty abstain answer from LLM")

            return {"answer": answer, "suggestions": suggestions, "sources": []}
        except Exception:
            return self._abstain_response()

    def _normalize_suggestions(self, suggestions: Any) -> List[Dict[str, str]]:
        if not isinstance(suggestions, list):
            return []
        normalized = []
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            value = str(item.get("value", "")).strip()
            if label and value:
                normalized.append({"label": label, "value": value})
        return normalized

    def _normalize_sources(self, sources: Any, answer: str) -> List[str]:
        if isinstance(sources, list):
            cleaned = []
            for item in sources:
                value = str(item).strip()
                if value:
                    cleaned.append(value)
            return list(dict.fromkeys(cleaned))
        extracted = self._extract_sources(answer)
        return extracted if extracted else []
    
    def _normalize_filters(self, filters: Any) -> Dict[str, Any]:
        if not isinstance(filters, dict) or not filters:
            return {}
        return {str(k).strip(): v for k, v in filters.items() if k and v is not None}

    def _extract_sql(self, text: str) -> Optional[str]:
        if not text:
            return None
        try:
            parsed = self._extract_json(text)
            sql = parsed.get("sql") or parsed.get("query")
            if sql:
                return str(sql).strip()
        except Exception:
            pass
        match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        candidate = match.group(1).strip() if match else text

        statements = sqlparse.parse(candidate)
        for statement in statements:
            if statement.get_type() == "SELECT":
                return str(statement).strip()

        fallback = re.search(r"SELECT\s+.*", candidate, flags=re.IGNORECASE | re.DOTALL)
        return fallback.group(0).strip() if fallback else None

    def search_similar_traces(self, query: str, min_rating: int = 4, limit: int = 3) -> str:
        results = self.store.search_similar_experiences(query, min_rating=min_rating, limit=limit)
        return json.dumps(results, default=str)

    def query(self, user_query: str, session_id: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a natural language query using the configured provider.
        
        Args:
            user_query: Natural language question about traces
            session_id: Conversation session ID for context
            model_id: Optional model override (e.g., 'gpt-4o', 'gemini-2.0-flash-exp')
        """
        if not LIBRARIAN_AVAILABLE:
            return {
                "answer": "Librarian is not available. Check provider configuration and API keys.",
                "suggestions": [],
                "sources": [],
            }

        # Select provider with optional model override
        provider = select_provider(model_override=model_id)

        history = self.store.get_chat_history(session_id)
        history_text = self._format_history(history)

        self.store.save_chat_message(session_id, "user", user_query)

        system_prompt = self._system_prompt()
        user_content = (
            "Conversation History:\n"
            f"{history_text}\n\n"
            "User Question:\n"
            f"{user_query}\n\n"
            "Return JSON only."
        )

        logger.debug("Librarian system prompt:\n%s", system_prompt)
        logger.debug("Librarian user content:\n%s", user_content)
        logger.debug("Librarian using provider: %s (model: %s)", provider.name, getattr(provider, 'model', getattr(provider, 'model_name', 'unknown')))

        try:
            if not provider.supports_tools:
                session = provider.start_chat(system_prompt, [])
                prompt = (
                    user_content
                    + "\n\nProvide a SQL SELECT query only (or JSON with key 'sql')."
                )
                for _ in range(3):
                    response = provider.send_user_message(session, prompt)
                    text = provider.extract_text(response)
                    sql_query = self._extract_sql(text)
                    if not sql_query:
                        prompt = "Failed to parse SQL. Please output a single SELECT query."
                        continue

                    tool_result = self.run_sql_query(sql_query)
                    if tool_result.startswith("EXECUTION_FAILED"):
                        prompt = (
                            "SQL execution failed. Here is the database error message. "
                            "Fix the SQL and output a new SELECT query only.\n"
                            f"ERROR: {tool_result}"
                        )
                        continue
                    if tool_result.startswith("EMPTY_RESULT"):
                        result = self._abstain_response_from_llm(user_query, history_text, provider)
                        self.store.save_chat_message(session_id, "assistant", result)
                        return result

                    prompt = (
                        "Here are the SQL results (JSON). Provide a JSON answer with keys "
                        "answer, suggestions, sources:\n"
                        f"{tool_result}"
                    )
                    response = provider.send_user_message(session, prompt)
                    answer_text = provider.extract_text(response)
                    try:
                        parsed = self._extract_json(answer_text)
                    except Exception:
                        parsed = {"answer": answer_text, "suggestions": [], "sources": None, "filters": {}}

                    answer = str(parsed.get("answer", "")).strip() or "No response."
                    suggestions = self._normalize_suggestions(parsed.get("suggestions"))
                    sources = self._normalize_sources(parsed.get("sources"), answer)
                    filters = self._normalize_filters(_validate_filters(parsed.get("filters") or {}) or {})
                    result = {"answer": answer, "suggestions": suggestions, "sources": sources, "filters": filters}
                    self.store.save_chat_message(session_id, "assistant", result)
                    return result

                fallback = "Unable to generate a valid SQL query. Please refine the question."
                self.store.save_chat_message(session_id, "assistant", {"answer": fallback})
                return {"answer": fallback, "suggestions": [], "sources": [], "filters": {}}

            session = provider.start_chat(system_prompt, self.tools)
            response = provider.send_user_message(session, user_content)
            last_sql_result: Optional[str] = None
            saw_sql_result = False
            extracted_filters = {}

            for _ in range(5):
                tool_calls = provider.extract_tool_calls(response)
                if not tool_calls:
                    break

                for call in tool_calls:
                    tool_name = call.get("name")
                    args = call.get("args") or {}
                    if tool_name == "run_sql_query":
                        sql_query = args.get("query", "")
                        tool_result = self.run_sql_query(sql_query)
                        if not tool_result.startswith("EXECUTION_FAILED") and not tool_result.startswith("EMPTY_RESULT"):
                            last_sql_result = tool_result
                            saw_sql_result = True
                        self.store.save_chat_message(
                            session_id,
                            "tool",
                            f"SQL: {sql_query}\nRESULT: {tool_result}",
                        )
                    elif tool_name == "search_similar_traces":
                        query = args.get("query", "")
                        min_rating = int(args.get("min_rating", 4))
                        limit = int(args.get("limit", 3))
                        tool_result = self.search_similar_traces(query, min_rating=min_rating, limit=limit)
                        self.store.save_chat_message(
                            session_id,
                            "tool",
                            f"SEARCH: {query}\nRESULT: {tool_result}",
                        )
                    elif tool_name == "set_api_filters":
                        extracted_filters = args
                        tool_result = "FILTERS_SET"
                    else:
                        tool_result = "UNKNOWN_TOOL"

                    response = provider.send_tool_result(
                        session,
                        tool_name=tool_name,
                        tool_result=tool_result,
                        tool_call_id=call.get("id"),
                    )

                    if tool_name == "run_sql_query" and tool_result.startswith("EXECUTION_FAILED"):
                        response = provider.send_user_message(
                            session,
                            (
                                "The SQL query failed. Use the error message to fix the query. "
                                "Return a corrected SQL query only.\n"
                                f"ERROR: {tool_result}"
                            ),
                        )
                        break
                    if tool_name == "run_sql_query" and tool_result.startswith("EMPTY_RESULT"):
                        result = self._abstain_response_from_llm(user_query, history_text, provider)
                        self.store.save_chat_message(session_id, "assistant", result)
                        return result

            if saw_sql_result and last_sql_result:
                response = provider.send_user_message(
                    session,
                    (
                        "Using the SQL results below, return ONLY a JSON object with keys "
                        "answer, suggestions, sources, filters. The answer must be a natural language summary.\n"
                        f"SQL_RESULTS: {last_sql_result}"
                    ),
                )

            answer_text = provider.extract_text(response)
            try:
                parsed = self._extract_json(answer_text)
            except Exception:
                parsed = {"answer": answer_text, "suggestions": [], "sources": None, "filters": {}}

            if self._extract_sql(str(parsed.get("answer", "")) or answer_text):
                response = provider.send_user_message(
                    session,
                    "Do not return SQL. Summarize the findings in natural language and return JSON only.",
                )
                answer_text = provider.extract_text(response)
                try:
                    parsed = self._extract_json(answer_text)
                except Exception:
                    parsed = {"answer": answer_text, "suggestions": [], "sources": None, "filters": {}}

            answer = str(parsed.get("answer", "")).strip() or "No response."
            suggestions = self._normalize_suggestions(parsed.get("suggestions"))
            sources = self._normalize_sources(parsed.get("sources"), answer)
            filters = self._normalize_filters(extracted_filters)

            result = {
                "answer": answer,
                "suggestions": suggestions,
                "sources": sources,
                "filters": filters,
            }

            self.store.save_chat_message(session_id, "assistant", result)
            return result

        except Exception as e:
            logger.exception("Librarian query failed for session %s", session_id)
            error_result = {
                "answer": f"Sorry, I encountered an error processing your query: {str(e)}\n\nPlease try rephrasing your question or check the server logs.",
                "suggestions": [],
                "sources": [],
                "filters": {},
            }
            self.store.save_chat_message(session_id, "assistant", error_result)
            raise