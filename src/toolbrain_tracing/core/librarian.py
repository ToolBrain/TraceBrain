"""
Librarian AI Agent for ToolBrain TraceStore Natural Language Queries

This module provides a provider-agnostic AI agent that can answer questions
about traces using function calling to query the TraceStore database.
It supports both API-hosted and open-source models across multiple providers.
"""

from typing import Dict, List, Optional, Any
from collections import Counter
from datetime import datetime, timedelta
import json
import logging
import re

import requests

from toolbrain_tracing.config import settings

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    pass


def _build_tool_specs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "list_recent_traces",
            "description": "Retrieves a list of the most recent agent execution traces from the TraceStore database. Use this when users ask for recent traces, latest traces, or want to see what traces exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of traces to retrieve (default: 5, max: 20)"
                    }
                }
            },
        },
        {
            "name": "get_trace_details",
            "description": "Retrieves detailed information about a specific trace, including all spans and their attributes. Use this when users ask for details about a specific trace ID or want to understand what happened in a particular trace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "The unique identifier of the trace (32-character hexadecimal string)"
                    }
                },
                "required": ["trace_id"],
            },
        },
        {
            "name": "search_traces_by_prompt",
            "description": "Searches for traces that contain a specific keyword in their system prompt. Use this when users want to find traces related to a specific topic or keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword to search for in system prompts"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)"
                    }
                },
                "required": ["keyword"],
            },
        },
        {
            "name": "get_tool_usage_stats",
            "description": "Retrieves statistics about which tools are being used most frequently across all traces. Use this when users ask about tool usage, most used tools, or tool statistics.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "get_database_statistics",
            "description": "Retrieves overall database statistics including total traces, spans, feedback counts, and other metrics. Use this when users ask 'how many traces', 'how many spans', or general database statistics.",
            "parameters": {"type": "object", "properties": {}},
        },
    ]


class BaseProvider:
    name = "base"
    supports_tools = False

    def __init__(self):
        self.timeout = settings.LLM_TIMEOUT
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        raise NotImplementedError

    def send_user_message(self, session, content: str):
        raise NotImplementedError

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        raise NotImplementedError

    def extract_text(self, response) -> str:
        raise NotImplementedError

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        return []


class OpenAIProvider(BaseProvider):
    name = "openai"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None):
        super().__init__()
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("openai SDK not available") from exc
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        messages = [{"role": "system", "content": system_instruction}]
        return {"messages": messages, "tools": tools}

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=session["messages"],
            tools=[{"type": "function", "function": tool} for tool in session.get("tools", [])],
            tool_choice="auto" if session.get("tools") else None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        message = response.choices[0].message
        session["messages"].append(message.model_dump())
        return response

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        tool_message = {
            "role": "tool",
            "name": tool_name,
            "content": tool_result,
        }
        if tool_call_id:
            tool_message["tool_call_id"] = tool_call_id
        session["messages"].append(tool_message)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=session["messages"],
            tools=[{"type": "function", "function": tool} for tool in session.get("tools", [])],
            tool_choice="auto" if session.get("tools") else None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        message = response.choices[0].message
        session["messages"].append(message.model_dump())
        return response

    def extract_text(self, response) -> str:
        return response.choices[0].message.content or ""

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        result: List[Dict[str, Any]] = []
        for call in tool_calls:
            args_raw = call.function.arguments or "{}"
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                args = {}
            result.append(
                {
                    "name": call.function.name,
                    "args": args,
                    "id": call.id,
                }
            )
        return result


class AzureOpenAIProvider(OpenAIProvider):
    name = "azure_openai"

    def __init__(self, api_key: Optional[str], model: str, base_url: str, api_version: str):
        try:
            from openai import AzureOpenAI
        except ImportError as exc:
            raise ProviderError("openai SDK not available") from exc
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=base_url,
            api_version=api_version,
        )
        self.model = model


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None):
        super().__init__()
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ProviderError("anthropic SDK not available") from exc
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.model = model

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        return {"system": system_instruction, "messages": [], "tools": tools}

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        response = self.client.messages.create(
            model=self.model,
            system=session["system"],
            messages=session["messages"],
            tools=[
                {
                    "name": tool["name"],
                    "description": tool.get("description"),
                    "input_schema": tool.get("parameters") or {"type": "object", "properties": {}},
                }
                for tool in session.get("tools", [])
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens or 512,
        )
        return response

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        session["messages"].append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": tool_result,
                    }
                ],
            }
        )
        response = self.client.messages.create(
            model=self.model,
            system=session["system"],
            messages=session["messages"],
            tools=[
                {
                    "name": tool["name"],
                    "description": tool.get("description"),
                    "input_schema": tool.get("parameters") or {"type": "object", "properties": {}},
                }
                for tool in session.get("tools", [])
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens or 512,
        )
        return response

    def extract_text(self, response) -> str:
        parts = response.content or []
        texts = [p.text for p in parts if getattr(p, "type", None) == "text"]
        return "".join(texts).strip()

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        parts = response.content or []
        result: List[Dict[str, Any]] = []
        for part in parts:
            if getattr(part, "type", None) == "tool_use":
                result.append(
                    {
                        "name": part.name,
                        "args": part.input or {},
                        "id": part.id,
                    }
                )
        return result




class OllamaProvider(BaseProvider):
    name = "ollama"
    supports_tools = False

    def __init__(self, base_url: Optional[str], model: str):
        super().__init__()
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.model = model

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        messages = [{"role": "system", "content": system_instruction}]
        return {"messages": messages}

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": session["messages"],
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        response = requests.post(
            f"{self.base_url}/api/chat", json=payload, timeout=self.timeout
        )
        if response.status_code >= 400:
            raise ProviderError(f"Provider error {response.status_code}: {response.text[:200]}")
        data = response.json()
        message = data.get("message") or {}
        session["messages"].append(message)
        return data

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        raise ProviderError("Ollama provider does not support tool calling")

    def extract_text(self, response) -> str:
        message = response.get("message") or {}
        return message.get("content", "") or ""


class GeminiProvider(BaseProvider):
    name = "gemini"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str):
        super().__init__()
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ProviderError("google-generativeai not available") from exc
        if not api_key:
            raise ProviderError("GEMINI_API_KEY or LLM_API_KEY is required for gemini")
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model_name = model

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        tool_decls = []
        for tool in tools:
            tool_decls.append(
                self.genai.protos.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description") or "",
                    parameters=self.genai.protos.Schema(
                        type=self.genai.protos.Type.OBJECT,
                        properties={
                            key: self.genai.protos.Schema(
                                type=self.genai.protos.Type.INTEGER
                                if val.get("type") == "integer"
                                else self.genai.protos.Type.STRING,
                                description=val.get("description", ""),
                            )
                            for key, val in (tool.get("parameters") or {}).get("properties", {}).items()
                        },
                        required=(tool.get("parameters") or {}).get("required") or [],
                    ),
                )
            )
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            tools=tool_decls,
            system_instruction=system_instruction,
        )
        chat = model.start_chat()
        return {"chat": chat}

    def send_user_message(self, session, content: str):
        return session["chat"].send_message(content)

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        return session["chat"].send_message(
            self.genai.protos.Content(
                parts=[
                    self.genai.protos.Part(
                        function_response=self.genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": tool_result},
                        )
                    )
                ]
            )
        )

    def extract_text(self, response) -> str:
        return response.text

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        if not response.candidates or not response.candidates[0].content.parts:
            return []
        tool_calls: List[Dict[str, Any]] = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                function_call = part.function_call
                tool_calls.append(
                    {
                        "name": function_call.name,
                        "args": dict(function_call.args),
                        "id": None,
                    }
                )
        return tool_calls


class HuggingFaceProvider(BaseProvider):
    name = "huggingface"
    supports_tools = False

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api-inference.huggingface.co").rstrip("/")

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        return {"system": system_instruction, "history": []}

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def send_user_message(self, session, content: str):
        session["history"].append({"role": "user", "content": content})
        prompt = session["system"] + "\n\n"
        for message in session["history"]:
            role = message.get("role", "user")
            prompt += f"{role.capitalize()}: {message.get('content', '')}\n"
        prompt += "Assistant:"

        payload: Dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
            },
        }
        if self.max_tokens:
            payload["parameters"]["max_new_tokens"] = self.max_tokens

        url = f"{self.base_url}/models/{self.model}"
        response = requests.post(url, headers=self._headers(), json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise ProviderError(f"Provider error {response.status_code}: {response.text[:200]}")

        data = response.json()
        session["history"].append({"role": "assistant", "content": self.extract_text(data)})
        return data

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        raise ProviderError("Hugging Face provider does not support tool calling")

    def extract_text(self, response) -> str:
        if isinstance(response, list) and response:
            if isinstance(response[0], dict):
                return response[0].get("generated_text", "") or ""
            return str(response[0])
        if isinstance(response, dict):
            return response.get("generated_text", "") or response.get("text", "") or ""
        return ""


def _select_provider() -> BaseProvider:
    mode = settings.LIBRARIAN_MODE.lower()
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    api_key = settings.LLM_API_KEY

    if provider == "gemini" and not api_key:
        api_key = settings.GEMINI_API_KEY

    if mode == "api":
        if provider == "gemini":
            return GeminiProvider(api_key=api_key, model=model)
        if provider in {"openai", "openai_compatible"}:
            base_url = settings.LLM_BASE_URL
            return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)
        if provider == "azure_openai":
            if not settings.LLM_BASE_URL or not settings.LLM_API_VERSION:
                raise ProviderError("LLM_BASE_URL and LLM_API_VERSION are required for azure_openai")
            return AzureOpenAIProvider(
                api_key=api_key,
                model=model,
                base_url=settings.LLM_BASE_URL,
                api_version=settings.LLM_API_VERSION,
            )
        if provider == "anthropic":
            return AnthropicProvider(api_key=api_key, model=model, base_url=settings.LLM_BASE_URL)
    else:
        if provider in {"huggingface", "hf", "gemini"}:
            if provider == "gemini":
                logger.warning("open_source mode uses Hugging Face by default")
            return HuggingFaceProvider(api_key=api_key, model=model, base_url=settings.LLM_BASE_URL)
        if provider in {"openai_compatible", "vllm", "tgi", "lmstudio"}:
            base_url = settings.LLM_BASE_URL or "http://localhost:8000"
            return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)
        if provider == "ollama":
            return OllamaProvider(base_url=settings.LLM_BASE_URL, model=model)

    raise ProviderError(f"Unsupported provider configuration: {mode} / {provider}")


def is_librarian_available() -> bool:
    try:
        _select_provider()
        return True
    except Exception as exc:
        logger.warning("Librarian unavailable: %s", exc)
        return False


LIBRARIAN_AVAILABLE = is_librarian_available()


class LibrarianAgent:
    """
    AI agent for natural language queries about traces.
    """

    def __init__(self, store):
        self.store = store
        self.tools = _build_tool_specs()
        self.function_map = {
            "list_recent_traces": self.list_recent_traces,
            "get_trace_details": self.get_trace_details,
            "search_traces_by_prompt": self.search_traces_by_prompt,
            "get_tool_usage_stats": self.get_tool_usage_stats,
            "get_database_statistics": self.get_database_statistics,
        }
        self.provider = _select_provider()

    def list_recent_traces(self, limit: int = 5) -> str:
        """Get list of recent traces."""
        try:
            limit = min(max(1, limit), 20)
            traces = self.store.list_traces(limit=limit, include_spans=True)

            if not traces:
                return "No traces found in the database."

            result = f"Found {len(traces)} recent traces:\n\n"

            for i, trace in enumerate(traces, 1):
                result += f"{i}. Trace ID: {trace.id}\n"
                result += f"   Created: {trace.created_at}\n"
                result += f"   Spans: {len(trace.spans)}\n"
                result += f"   System Prompt: {trace.system_prompt[:80] if trace.system_prompt else 'N/A'}...\n"

                if trace.feedback:
                    rating = trace.feedback.get("rating", "N/A")
                    result += f"   Feedback: Rating {rating}/5\n"

                result += "\n"

            return result

        except Exception as e:
            return f"Error retrieving traces: {str(e)}"

    def get_trace_details(self, trace_id: str) -> str:
        """Get detailed information about a specific trace."""
        try:
            trace = self.store.get_trace(trace_id)

            if not trace:
                return f"Trace with ID '{trace_id}' not found."

            result = f"Trace Details: {trace.id}\n"
            result += "=" * 70 + "\n\n"

            result += f"System Prompt: {trace.system_prompt or 'N/A'}\n"
            result += f"Created: {trace.created_at}\n"

            if trace.feedback:
                fb = trace.feedback
                result += f"Feedback: Rating {fb.get('rating', 'N/A')}/5"
                if fb.get("comment"):
                    result += f" - {fb['comment']}"
                result += "\n"

            result += f"\nTotal Spans: {len(trace.spans)}\n"
            result += "\n" + "-" * 70 + "\n\n"

            for i, span in enumerate(trace.spans, 1):
                attrs = span.attributes or {}

                result += f"Span {i}: {span.name}\n"
                result += f"  ID: {span.span_id}\n"
                result += f"  Parent: {span.parent_id or 'None (root)'}\n"
                result += f"  Time: {span.start_time or 'N/A'} -> {span.end_time or 'N/A'}\n"

                span_type = attrs.get("toolbrain.span.type", "unknown")
                result += f"  Type: {span_type}\n"

                if span_type == "llm_inference":
                    thought = attrs.get("toolbrain.llm.thought")
                    tool_code = attrs.get("toolbrain.llm.tool_code")
                    final_answer = attrs.get("toolbrain.llm.final_answer")

                    if thought:
                        result += f"  Thought: {thought}\n"
                    if tool_code:
                        result += f"  Tool Call: {tool_code}\n"
                    if final_answer:
                        result += f"  Final Answer: {final_answer}\n"

                elif span_type == "tool_execution":
                    tool_name = attrs.get("toolbrain.tool.name", "unknown")
                    tool_input = attrs.get("toolbrain.tool.input", "N/A")
                    tool_output = attrs.get("toolbrain.tool.output", "N/A")

                    result += f"  Tool: {tool_name}\n"
                    result += f"  Input: {tool_input}\n"
                    result += f"  Output: {tool_output}\n"

                    if attrs.get("otel.status_code") == "ERROR":
                        result += f"  Error: {attrs.get('otel.status_description', 'Unknown error')}\n"

                result += "\n"

            return result

        except Exception as e:
            return f"Error retrieving trace details: {str(e)}"

    def search_traces_by_prompt(self, keyword: str, limit: int = 10) -> str:
        """Search traces by keyword in system prompt."""
        try:
            all_traces = self.store.list_traces(limit=limit, include_spans=True)

            matching_traces = [
                t for t in all_traces
                if keyword.lower() in (t.system_prompt or "").lower()
            ]

            if not matching_traces:
                return f"No traces found with keyword '{keyword}' in system prompt."

            result = f"Found {len(matching_traces)} trace(s) matching '{keyword}':\n\n"

            for i, trace in enumerate(matching_traces, 1):
                result += f"{i}. Trace ID: {trace.id}\n"
                result += f"   System Prompt: {trace.system_prompt or 'N/A'}\n"
                result += f"   Spans: {len(trace.spans)}\n\n"

            return result

        except Exception as e:
            return f"Error searching traces: {str(e)}"

    def get_tool_usage_stats(self) -> str:
        """Get tool usage statistics."""
        try:
            from toolbrain_tracing.db.base import Span

            session = self.store.get_session()
            try:
                tool_spans = session.query(Span).filter(
                    Span.attributes.contains({"toolbrain.span.type": "tool_execution"})
                ).all()

                if not tool_spans:
                    return "No tool execution data found in the database."

                tool_counts = Counter()

                for span in tool_spans:
                    tool_name = span.attributes.get("toolbrain.tool.name", "unknown")
                    tool_counts[tool_name] += 1

                result = "Tool Usage Statistics:\n\n"
                result += f"Total tool calls: {sum(tool_counts.values())}\n"
                result += f"Unique tools used: {len(tool_counts)}\n\n"
                result += "Most used tools:\n"

                for i, (tool_name, count) in enumerate(tool_counts.most_common(10), 1):
                    percentage = (count / sum(tool_counts.values())) * 100
                    result += f"{i}. {tool_name}: {count} calls ({percentage:.1f}%)\n"

                return result

            finally:
                session.close()

        except Exception as e:
            return f"Error retrieving tool usage stats: {str(e)}"

    def get_database_statistics(self) -> str:
        """Get overall database statistics."""
        try:
            from toolbrain_tracing.db.base import Trace, Span

            session = self.store.get_session()
            try:
                total_traces = session.query(Trace).count()
                total_spans = session.query(Span).count()
                traces_with_feedback = session.query(Trace).filter(Trace.feedback.isnot(None)).count()

                yesterday = datetime.utcnow() - timedelta(days=1)
                traces_last_24h = session.query(Trace).filter(Trace.created_at >= yesterday).count()

                avg_spans = total_spans / total_traces if total_traces > 0 else 0

                result = "Database Statistics:\n\n"
                result += f"Total Traces: {total_traces}\n"
                result += f"Total Spans: {total_spans}\n"
                result += f"Average Spans per Trace: {avg_spans:.1f}\n"
                result += f"Traces with Feedback: {traces_with_feedback}\n"
                result += f"Traces created in last 24h: {traces_last_24h}\n"

                return result

            finally:
                session.close()

        except Exception as e:
            return f"Error retrieving database statistics: {str(e)}"

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a natural language query using the configured provider.

        Returns:
            Dictionary with 'answer' and optional 'sources' (trace IDs)
        """
        if not LIBRARIAN_AVAILABLE:
            return {
                "answer": "Librarian is not available. Check provider configuration and API keys.",
                "sources": None,
            }

        try:
            system_instruction = """You are the ToolBrain TraceStore Librarian, an expert AI assistant specialized in helping users explore and understand agent execution traces.

Your role:
- Help users find and analyze traces stored in the ToolBrain TraceStore database
- Use the provided functions to query the database
- Provide clear, well-formatted summaries of trace data
- Explain what happened during agent execution based on span data
- Answer statistical questions about the database

Guidelines:
- Always use functions to fetch data; never make up trace information
- When showing trace details, highlight important attributes like thoughts, tool calls, and outputs
- If a user asks for "recent traces" or "latest traces", use list_recent_traces
- If a user asks "how many traces" or statistics, use get_database_statistics
- If a user asks about tool usage or "what tools are used", use get_tool_usage_stats
- If a user provides a specific trace ID, use get_trace_details
- Format your responses clearly with proper structure
- Be concise but informative

Remember: You are a helpful librarian. Be informative, accurate, and user-friendly!"""

            session = self.provider.start_chat(system_instruction, self.tools)
            response = self.provider.send_user_message(session, user_query)

            if settings.LLM_DEBUG:
                logger.info("LLM provider=%s initial response text: %s", self.provider.name, self.provider.extract_text(response))

            tool_calls = []
            for _ in range(5):
                tool_calls = self.provider.extract_tool_calls(response)
                if not tool_calls:
                    break

                for call in tool_calls:
                    name = call.get("name")
                    args = call.get("args") or {}
                    call_id = call.get("id")

                    if name in self.function_map:
                        function_result = self.function_map[name](**args)
                    else:
                        function_result = f"Unknown tool: {name}"

                    response = self.provider.send_tool_result(
                        session,
                        tool_name=name,
                        tool_result=function_result,
                        tool_call_id=call_id,
                    )

            if not tool_calls:
                fallback = self._fallback_tool_for_query(user_query)
                if fallback:
                    if settings.LLM_DEBUG:
                        logger.info("LLM fallback tool used: %s", fallback[0])
                    answer = self.function_map[fallback[0]](**fallback[1])
                    return {
                        "answer": answer,
                        "sources": self._extract_sources(answer),
                    }

            answer = self.provider.extract_text(response)

            trace_ids = self._extract_sources(answer)

            return {
                "answer": answer,
                "sources": trace_ids,
            }

        except Exception as e:
            logger.exception("Librarian query error")
            return {
                "answer": f"Sorry, I encountered an error processing your query: {str(e)}\n\nPlease try rephrasing your question.",
                "sources": None,
            }

    def _extract_sources(self, answer: str) -> Optional[List[str]]:
        potential_ids = re.findall(r"[a-f0-9]{32}", answer)
        return list(set(potential_ids)) if potential_ids else None

    def _fallback_tool_for_query(self, user_query: str) -> Optional[tuple[str, Dict[str, Any]]]:
        query = user_query.lower()
        trace_ids = re.findall(r"[a-f0-9]{32}", query)
        if trace_ids:
            return ("get_trace_details", {"trace_id": trace_ids[0]})

        if "recent" in query or "latest" in query:
            return ("list_recent_traces", {"limit": 5})

        if "how many" in query or "stats" in query or "statistics" in query:
            return ("get_database_statistics", {})

        if "tool usage" in query or "most used tools" in query or "tool stats" in query:
            return ("get_tool_usage_stats", {})

        return None
