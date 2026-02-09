"""
Librarian AI Agent for ToolBrain TraceStore Natural Language Queries

This module provides a provider-agnostic text-to-SQL agent with conversational
memory, self-correction, and interactive abstention.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import re

from toolbrain_tracing.config import settings
from toolbrain_tracing.core.llm_providers import select_provider, is_provider_available

logger = logging.getLogger(__name__)


SCHEMA_CONTEXT = """
PostgreSQL schema (read-only):

Table: traces
- id (string, primary key)
- system_prompt (text)
- episode_id (string)
- created_at (timestamp)
- feedback (jsonb)

Table: spans
- id (integer, primary key)
- span_id (string)
- trace_id (string, foreign key -> traces.id)
- parent_id (string)
- name (string)
- start_time (timestamp)
- end_time (timestamp)
- attributes (jsonb)

JSONB usage examples:
- spans.attributes->>'toolbrain.span.type'
- spans.attributes->>'toolbrain.tool.name'
- spans.attributes->>'otel.status_code'
- traces.feedback->>'rating'

Join examples:
- spans.trace_id = traces.id
""".strip()


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
    ]


LIBRARIAN_AVAILABLE = is_provider_available()


class LibrarianAgent:
    """Text-to-SQL agent with conversational memory and self-correction."""

    def __init__(self, store):
        self.store = store
        self.tools = _build_tool_specs()
        self.provider = select_provider()

    def _system_prompt(self) -> str:
        return (
            "You are the ToolBrain TraceStore Librarian, a text-to-SQL assistant. "
            "Use the run_sql_query tool for ALL database access. "
            "Only write SELECT queries. "
            "If the SQL execution fails, correct the query and try again. "
            "If the tool returns EMPTY_RESULT, do NOT hallucinate. Instead, ask a clarifying question and return JSON with suggestions. "
            "Always output a JSON object with keys: answer, suggestions, sources.\n\n"
            f"{SCHEMA_CONTEXT}"
        )

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
                {"label": "Search by episode", "value": "Filter by toolbrain.episode.id"},
                {"label": "Search by tool", "value": "Filter by toolbrain.tool.name"},
            ],
            "sources": [],
        }

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

        match = re.search(r"SELECT\s+.*", text, flags=re.IGNORECASE | re.DOTALL)
        return match.group(0).strip() if match else None

    def query(self, user_query: str, session_id: str) -> Dict[str, Any]:
        """Process a natural language query using the configured provider."""
        if not LIBRARIAN_AVAILABLE:
            return {
                "answer": "Librarian is not available. Check provider configuration and API keys.",
                "suggestions": [],
                "sources": None,
            }

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

        if not self.provider.supports_tools:
            session = self.provider.start_chat(system_prompt, [])
            prompt = (
                user_content
                + "\n\nProvide a SQL SELECT query only (or JSON with key 'sql')."
            )
            for _ in range(3):
                response = self.provider.send_user_message(session, prompt)
                text = self.provider.extract_text(response)
                sql_query = self._extract_sql(text)
                if not sql_query:
                    prompt = "Failed to parse SQL. Please output a single SELECT query."
                    continue

                tool_result = self.run_sql_query(sql_query)
                if tool_result.startswith("EXECUTION_FAILED"):
                    prompt = f"SQL error: {tool_result}. Please fix and output a new SELECT query."
                    continue
                if tool_result.startswith("EMPTY_RESULT"):
                    result = self._abstain_response()
                    self.store.save_chat_message(session_id, "assistant", result["answer"])
                    return result

                prompt = (
                    "Here are the SQL results (JSON). Provide a JSON answer with keys "
                    "answer, suggestions, sources:\n"
                    f"{tool_result}"
                )
                response = self.provider.send_user_message(session, prompt)
                answer_text = self.provider.extract_text(response)
                try:
                    parsed = self._extract_json(answer_text)
                except Exception:
                    parsed = {"answer": answer_text, "suggestions": [], "sources": None}

                answer = str(parsed.get("answer", "")).strip() or "No response."
                suggestions = self._normalize_suggestions(parsed.get("suggestions"))
                sources = parsed.get("sources") or self._extract_sources(answer)
                result = {"answer": answer, "suggestions": suggestions, "sources": sources}
                self.store.save_chat_message(session_id, "assistant", answer)
                return result

            fallback = "Unable to generate a valid SQL query. Please refine the question."
            self.store.save_chat_message(session_id, "assistant", fallback)
            return {"answer": fallback, "suggestions": [], "sources": None}

        session = self.provider.start_chat(system_prompt, self.tools)
        response = self.provider.send_user_message(session, user_content)

        for _ in range(3):
            tool_calls = self.provider.extract_tool_calls(response)
            if not tool_calls:
                break

            for call in tool_calls:
                sql_query = (call.get("args") or {}).get("query", "")
                tool_result = self.run_sql_query(sql_query)
                self.store.save_chat_message(
                    session_id,
                    "tool",
                    f"SQL: {sql_query}\nRESULT: {tool_result}",
                )
                response = self.provider.send_tool_result(
                    session,
                    tool_name="run_sql_query",
                    tool_result=tool_result,
                    tool_call_id=call.get("id"),
                )

                if tool_result.startswith("EXECUTION_FAILED"):
                    break
                if tool_result.startswith("EMPTY_RESULT"):
                    result = self._abstain_response()
                    self.store.save_chat_message(session_id, "assistant", result["answer"])
                    return result

        answer_text = self.provider.extract_text(response)
        try:
            parsed = self._extract_json(answer_text)
        except Exception:
            parsed = {"answer": answer_text, "suggestions": [], "sources": None}

        answer = str(parsed.get("answer", "")).strip() or "No response."
        suggestions = self._normalize_suggestions(parsed.get("suggestions"))
        sources = parsed.get("sources") or self._extract_sources(answer)

        result = {
            "answer": answer,
            "suggestions": suggestions,
            "sources": sources,
        }

        self.store.save_chat_message(session_id, "assistant", answer)
        return result
