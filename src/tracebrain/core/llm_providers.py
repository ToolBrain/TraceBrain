"""Shared LLM provider selection and implementations."""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from functools import lru_cache
import logging
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

from tracebrain.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def is_running_in_docker() -> bool:
    """Best-effort detection for containerized runtime."""
    if Path("/.dockerenv").exists():
        return True

    cgroup_paths = ("/proc/1/cgroup", "/proc/self/cgroup")
    markers = ("docker", "containerd", "kubepods")
    for cgroup_path in cgroup_paths:
        try:
            payload = Path(cgroup_path).read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        if any(marker in payload for marker in markers):
            return True

    return False


def _is_localhost_url(url: Optional[str]) -> bool:
    endpoint = str(url or "").strip().lower()
    if not endpoint:
        return False

    try:
        hostname = urlparse(endpoint).hostname
    except Exception:
        hostname = None

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True

    # Fallback for malformed URLs or raw host:port style values.
    return "localhost" in endpoint or "127.0.0.1" in endpoint


def extract_usage_from_response(provider: str, response: Any) -> Optional[Dict[str, Any]]:
    provider_key = (provider or "").lower()
    if provider_key in {"openai", "azure_openai", "openai_compatible"}:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None

        if isinstance(usage, dict):
            raw = usage
        else:
            raw = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
                "cached_tokens": getattr(usage, "cached_tokens", None),
                "reasoning_tokens": getattr(usage, "reasoning_tokens", None),
                "input_tokens_details": getattr(usage, "input_tokens_details", None),
                "output_tokens_details": getattr(usage, "output_tokens_details", None),
            }

        prompt_tokens = raw.get("prompt_tokens", raw.get("input_tokens"))
        completion_tokens = raw.get("completion_tokens", raw.get("output_tokens"))
        total_tokens = raw.get("total_tokens")
        if total_tokens is None and isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        usage_out = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        if raw.get("cached_tokens") is not None:
            usage_out["cached_tokens"] = raw.get("cached_tokens")
        if raw.get("reasoning_tokens") is not None:
            usage_out["reasoning_tokens"] = raw.get("reasoning_tokens")
        if raw.get("input_tokens_details") is not None:
            usage_out["input_tokens_details"] = raw.get("input_tokens_details")
        if raw.get("output_tokens_details") is not None:
            usage_out["output_tokens_details"] = raw.get("output_tokens_details")

        if not any(isinstance(val, (int, float)) for val in usage_out.values()):
            return None
        return usage_out

    if provider_key == "anthropic":
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None

        if isinstance(usage, dict):
            prompt_tokens = usage.get("input_tokens")
            completion_tokens = usage.get("output_tokens")
        else:
            prompt_tokens = getattr(usage, "input_tokens", None)
            completion_tokens = getattr(usage, "output_tokens", None)

        if prompt_tokens is None and completion_tokens is None:
            return None

        total_tokens = None
        if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    if provider_key == "gemini":
        usage = getattr(response, "usage_metadata", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage_metadata") or response.get("usageMetadata")
        if usage is None:
            return None

        if isinstance(usage, dict):
            raw = usage
        else:
            raw = {
                "prompt_token_count": getattr(usage, "prompt_token_count", None),
                "response_token_count": getattr(usage, "response_token_count", None),
                "total_token_count": getattr(usage, "total_token_count", None),
                "cached_content_token_count": getattr(usage, "cached_content_token_count", None),
                "thoughts_token_count": getattr(usage, "thoughts_token_count", None),
                "prompt_tokens_details": getattr(usage, "prompt_tokens_details", None),
                "response_tokens_details": getattr(usage, "response_tokens_details", None),
            }

        prompt_tokens = raw.get("prompt_token_count")
        completion_tokens = raw.get("response_token_count")
        total_tokens = raw.get("total_token_count")
        if total_tokens is None and isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        usage_out = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        if raw.get("cached_content_token_count") is not None:
            usage_out["cached_tokens"] = raw.get("cached_content_token_count")
        if raw.get("thoughts_token_count") is not None:
            usage_out["reasoning_tokens"] = raw.get("thoughts_token_count")
        if raw.get("prompt_tokens_details") is not None:
            usage_out["prompt_tokens_details"] = raw.get("prompt_tokens_details")
        if raw.get("response_tokens_details") is not None:
            usage_out["response_tokens_details"] = raw.get("response_tokens_details")

        if not any(isinstance(val, (int, float)) for val in usage_out.values()):
            return None
        return usage_out

    return None


class ProviderError(RuntimeError):
    pass


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

    def extract_usage(self, response) -> Optional[Dict[str, Any]]:
        return None

    def _extract_status_code(self, exc: Exception) -> Optional[int]:
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return status_code

        response = getattr(exc, "response", None)
        if response is not None:
            response_code = getattr(response, "status_code", None)
            if isinstance(response_code, int):
                return response_code

        return None

    def _is_timeout(self, exc: Exception) -> bool:
        if isinstance(exc, TimeoutError):
            return True
        if isinstance(exc, requests.exceptions.Timeout):
            return True

        try:
            import httpx

            if isinstance(exc, httpx.TimeoutException):
                return True
        except Exception:
            pass

        return False

    def _is_connection_error(self, exc: Exception) -> bool:
        if isinstance(exc, requests.exceptions.ConnectionError):
            return True

        # Walk wrapped exception chain (SDK wrappers often store the root cause in __cause__).
        seen: set[int] = set()
        cursor: Optional[BaseException] = exc
        while cursor is not None and id(cursor) not in seen:
            seen.add(id(cursor))

            if isinstance(cursor, requests.exceptions.ConnectionError):
                return True

            class_name = cursor.__class__.__name__.lower()
            if class_name in {"apiconnectionerror", "connecterror", "connectionerror"}:
                return True

            try:
                import httpx

                if isinstance(cursor, (httpx.ConnectError, httpx.NetworkError)):
                    return True
            except Exception:
                pass

            cursor = getattr(cursor, "__cause__", None) or getattr(cursor, "__context__", None)

        return False

    def _friendly_error_message(self, exc: Exception, endpoint_url: Optional[str] = None) -> str:
        try:
            from google.api_core.exceptions import ResourceExhausted

            if isinstance(exc, ResourceExhausted):
                return (
                    "System is busy. Too many requests to the AI provider. "
                    "Please wait a minute or switch models."
                )
        except Exception:
            pass

        if self._is_timeout(exc):
            return "The AI is taking too long to think. Please try again or use a smaller model."

        if self._is_connection_error(exc):
            message = (
                "Could not connect to the AI provider endpoint. "
                "Please verify the base URL and ensure the service is running."
            )
            if is_running_in_docker() and _is_localhost_url(endpoint_url):
                message += (
                    " Connection failed. Since you are running in Docker, you may need to use "
                    "'host.docker.internal' instead of 'localhost' to reach services on your host machine."
                )
            return message

        status_code = self._extract_status_code(exc)
        if status_code == 429:
            return (
                "System is busy. Too many requests to the AI provider. "
                "Please wait a minute or switch models."
            )
        if status_code == 400:
            return (
                "This model doesn't support the current request format or tool usage. "
                "Try a different model."
            )
        if status_code in {500, 503}:
            return "The AI provider's server is currently down or overloaded."

        return "The AI provider encountered an unexpected error. Please try again or switch models."

    def _raise_provider_error(
        self,
        exc: Exception,
        provider_label: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        label = provider_label or self.name
        logger.warning("%s provider error: %s", label, exc)
        raise ProviderError(self._friendly_error_message(exc, endpoint_url=endpoint_url)) from exc


class OpenAIProvider(BaseProvider):
    name = "openai"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None):
        super().__init__()
        try:
            from openai import OpenAI, APIStatusError, BadRequestError, NotFoundError
        except ImportError as exc:
            raise ProviderError("openai SDK not available") from exc
        self.base_url = str(base_url).strip().rstrip("/") if base_url else None
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self._NotFoundError = NotFoundError
        self._BadRequestError = BadRequestError
        self._APIStatusError = APIStatusError
        self._responses_supported: Optional[bool] = None

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        return {
            "system": system_instruction,
            "messages": [],
            "tools": tools,
            "tool_call_names": {},
        }

    @staticmethod
    def _read_output_field(item: Any, key: str) -> Any:
        if isinstance(item, dict):
            return item.get(key)
        return getattr(item, key, None)

    @staticmethod
    def _read_chat_field(item: Any, key: str) -> Any:
        if isinstance(item, dict):
            return item.get(key)
        return getattr(item, key, None)

    def _content_blocks_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return ""

        texts: List[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            text_value = block.get("text")
            if isinstance(text_value, str):
                texts.append(text_value)
        return "".join(texts).strip()

    def _build_responses_tool_specs(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_specs: List[Dict[str, Any]] = []
        for tool in tools or []:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue

            spec: Dict[str, Any] = {
                "type": "function",
                "name": name,
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
            }
            description = tool.get("description")
            if isinstance(description, str) and description.strip():
                spec["description"] = description
            tool_specs.append(spec)
        return tool_specs

    def _build_chat_tool_specs(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chat_tools: List[Dict[str, Any]] = []
        for tool in tools or []:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue

            function_payload: Dict[str, Any] = {
                "name": name,
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
            }
            description = tool.get("description")
            if isinstance(description, str) and description.strip():
                function_payload["description"] = description

            chat_tools.append({"type": "function", "function": function_payload})
        return chat_tools

    def _should_fallback_to_chat(self, exc: Exception) -> bool:
        status_code = self._extract_status_code(exc)
        if isinstance(exc, self._NotFoundError):
            return True
        if isinstance(exc, self._APIStatusError) and status_code in {404, 405}:
            return True

        if isinstance(exc, self._BadRequestError) and status_code == 400:
            message = str(exc).lower()
            fallback_markers = (
                "responses",
                "not found",
                "method not allowed",
                "unsupported",
                "does not exist",
                "unknown",
            )
            if any(marker in message for marker in fallback_markers):
                return True

        return status_code in {404, 405}

    def _append_function_calls_to_session(self, session: Dict[str, Any], response: Any) -> bool:
        """Persist assistant outputs and function calls so follow-up tool outputs keep valid context."""
        output_items = (
            response.get("output")
            if isinstance(response, dict)
            else getattr(response, "output", None)
        ) or []

        appended_assistant_message = False

        for item in output_items:
            item_type = self._read_output_field(item, "type")
            if item_type == "message":
                role = self._read_output_field(item, "role") or "assistant"
                content = self._read_output_field(item, "content")
                if role == "assistant" and isinstance(content, list) and content:
                    session["messages"].append({"role": "assistant", "content": content})
                    appended_assistant_message = True
                elif role == "assistant" and isinstance(content, str) and content.strip():
                    session["messages"].append({"role": "assistant", "content": content})
                    appended_assistant_message = True
                continue

            if item_type != "function_call":
                continue

            fn_payload = self._read_output_field(item, "function")
            call_id = (
                self._read_output_field(item, "call_id")
                or self._read_output_field(item, "id")
                or self._read_output_field(fn_payload, "call_id")
            )
            name = (
                self._read_output_field(item, "name")
                or self._read_output_field(fn_payload, "name")
            )
            arguments = (
                self._read_output_field(item, "arguments")
                or self._read_output_field(item, "args")
                or self._read_output_field(fn_payload, "arguments")
                or self._read_output_field(fn_payload, "args")
                or "{}"
            )

            if not call_id or not name:
                continue

            if not isinstance(arguments, str):
                try:
                    arguments = json.dumps(arguments)
                except Exception:
                    arguments = "{}"

            session["messages"].append(
                {
                    "type": "function_call",
                    "call_id": str(call_id),
                    "name": str(name),
                    "arguments": arguments,
                }
            )
            session.setdefault("tool_call_names", {})[str(call_id)] = str(name)

        return appended_assistant_message

    def _to_chat_messages(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        chat_messages: List[Dict[str, Any]] = []
        system_instruction = session.get("system")
        if isinstance(system_instruction, str) and system_instruction.strip():
            chat_messages.append({"role": "system", "content": system_instruction})

        tool_name_map = session.setdefault("tool_call_names", {})
        for message in session.get("messages", []) or []:
            if not isinstance(message, dict):
                continue

            message_type = message.get("type")
            if message_type == "function_call":
                call_id = str(message.get("call_id") or "").strip()
                name = str(message.get("name") or "").strip()
                arguments = message.get("arguments") or "{}"

                if not call_id or not name:
                    continue
                if not isinstance(arguments, str):
                    try:
                        arguments = json.dumps(arguments)
                    except Exception:
                        arguments = "{}"

                tool_name_map[call_id] = name
                chat_messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {"name": name, "arguments": arguments},
                            }
                        ],
                    }
                )
                continue

            if message_type == "function_call_output":
                call_id = str(message.get("call_id") or "").strip()
                if not call_id:
                    continue
                output = message.get("output")
                if not isinstance(output, str):
                    try:
                        output = json.dumps(output)
                    except Exception:
                        output = str(output or "")

                tool_name = tool_name_map.get(call_id) or "tool"
                chat_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": tool_name,
                        "content": output,
                    }
                )
                continue

            role = str(message.get("role") or "").strip()
            if role not in {"user", "assistant", "tool"}:
                continue

            content = message.get("content")
            if isinstance(content, str):
                normalized_content = content
            elif isinstance(content, list):
                normalized_content = self._content_blocks_to_text(content)
            else:
                normalized_content = ""

            if role == "tool":
                tool_message: Dict[str, Any] = {
                    "role": "tool",
                    "content": normalized_content,
                }
                tool_call_id = message.get("tool_call_id")
                if isinstance(tool_call_id, str) and tool_call_id.strip():
                    tool_message["tool_call_id"] = tool_call_id
                tool_name = message.get("name")
                if isinstance(tool_name, str) and tool_name.strip():
                    tool_message["name"] = tool_name
                chat_messages.append(tool_message)
                continue

            chat_messages.append({"role": role, "content": normalized_content})

        return chat_messages

    def _extract_chat_message(self, response: Any) -> Optional[Any]:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if not choices:
                return None
            return choices[0].get("message")

        choices = getattr(response, "choices", None) or []
        if not choices:
            return None
        return getattr(choices[0], "message", None)

    def _append_chat_completion_to_session(self, session: Dict[str, Any], response: Any) -> bool:
        message = self._extract_chat_message(response)
        if not message:
            return False

        appended_assistant_message = False

        content = self._read_chat_field(message, "content")
        if isinstance(content, str) and content.strip():
            session["messages"].append({"role": "assistant", "content": content})
            appended_assistant_message = True
        elif isinstance(content, list):
            text = self._content_blocks_to_text(content)
            if text:
                session["messages"].append({"role": "assistant", "content": text})
                appended_assistant_message = True

        tool_calls = self._read_chat_field(message, "tool_calls") or []
        for call in tool_calls:
            fn_payload = self._read_chat_field(call, "function")
            call_id = self._read_chat_field(call, "id")
            name = self._read_chat_field(call, "name") or self._read_chat_field(fn_payload, "name")
            arguments = (
                self._read_chat_field(call, "arguments")
                or self._read_chat_field(fn_payload, "arguments")
                or "{}"
            )
            if not call_id or not name:
                continue

            if not isinstance(arguments, str):
                try:
                    arguments = json.dumps(arguments)
                except Exception:
                    arguments = "{}"

            session["messages"].append(
                {
                    "type": "function_call",
                    "call_id": str(call_id),
                    "name": str(name),
                    "arguments": arguments,
                }
            )
            session.setdefault("tool_call_names", {})[str(call_id)] = str(name)

        return appended_assistant_message

    def _normalize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for message in messages or []:
            if not isinstance(message, dict):
                continue

            content = message.get("content")
            if isinstance(content, str):
                role = str(message.get("role") or "")
                block_type = "output_text" if role == "assistant" else "input_text"

                # Responses API accepts structured content blocks; normalize plain strings for compatibility.
                normalized_message = dict(message)
                normalized_message["content"] = [{"type": block_type, "text": content}]
                normalized.append(normalized_message)
            else:
                normalized.append(message)
        return normalized

    def _send_response(self, session):
        tool_specs = self._build_responses_tool_specs(session.get("tools", []))

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "instructions": session.get("system"),
            "input": self._normalize_messages(session.get("messages", [])),
            "temperature": self.temperature,
        }
        if tool_specs:
            request_kwargs["tools"] = tool_specs
        if self.max_tokens is not None:
            request_kwargs["max_output_tokens"] = self.max_tokens

        use_chat_fallback = self._responses_supported is False
        if not use_chat_fallback:
            try:
                response = self.client.responses.create(**request_kwargs)
                self._responses_supported = True
                appended_assistant_message = self._append_function_calls_to_session(session, response)
                output_text = getattr(response, "output_text", None)
                if isinstance(output_text, str) and output_text and not appended_assistant_message:
                    session["messages"].append({"role": "assistant", "content": output_text})
                return response
            except Exception as exc:
                if self._should_fallback_to_chat(exc):
                    self._responses_supported = False
                    logger.debug(
                        "Responses API not supported by provider. Falling back to Chat Completions API."
                    )
                else:
                    self._raise_provider_error(exc, "OpenAI", endpoint_url=self.base_url)
                    raise

        chat_request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": self._to_chat_messages(session),
            "temperature": self.temperature,
        }
        chat_tools = self._build_chat_tool_specs(session.get("tools", []))
        if chat_tools:
            chat_request_kwargs["tools"] = chat_tools
            chat_request_kwargs["tool_choice"] = "auto"
        if self.max_tokens is not None:
            chat_request_kwargs["max_tokens"] = self.max_tokens

        try:
            response = self.client.chat.completions.create(**chat_request_kwargs)
        except Exception as exc:
            self._raise_provider_error(exc, "OpenAI", endpoint_url=self.base_url)
            raise

        self._append_chat_completion_to_session(session, response)
        return response

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        return self._send_response(session)

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        if not isinstance(tool_result, str):
            tool_result = json.dumps(tool_result)

        if tool_call_id:
            tool_message = {
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": tool_result,
            }
        else:
            tool_message = {
                "role": "tool",
                "name": tool_name,
                "content": tool_result,
            }
        session["messages"].append(tool_message)
        return self._send_response(session)

    def extract_text(self, response) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            return output_text

        message = self._extract_chat_message(response)
        if not message:
            return ""

        content = self._read_chat_field(message, "content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return self._content_blocks_to_text(content)
        return ""

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        if isinstance(response, dict):
            output_items = response.get("output") or response.get("output_tool_calls") or []
        else:
            output_items = (
                getattr(response, "output", None)
                or getattr(response, "output_tool_calls", None)
                or []
            )
        result: List[Dict[str, Any]] = []

        def _read(item: Any, key: str) -> Any:
            if isinstance(item, dict):
                return item.get(key)
            return getattr(item, key, None)

        for item in output_items:
            item_type = _read(item, "type")
            if item_type and item_type not in {"tool_call", "function_call"}:
                continue

            fn_payload = _read(item, "function")
            name = _read(item, "name") or _read(fn_payload, "name")
            args_raw = (
                _read(item, "arguments")
                or _read(item, "args")
                or _read(fn_payload, "arguments")
                or _read(fn_payload, "args")
                or "{}"
            )
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                args = {}

            call_id = _read(item, "call_id") or _read(item, "id") or _read(fn_payload, "call_id")
            if not name:
                continue
            result.append(
                {
                    "name": name,
                    "args": args,
                    "id": call_id,
                }
            )
        if result:
            return result

        message = self._extract_chat_message(response)
        if not message:
            return []

        chat_tool_calls = self._read_chat_field(message, "tool_calls") or []
        normalized_tool_calls: List[Dict[str, Any]] = []
        for call in chat_tool_calls:
            fn_payload = self._read_chat_field(call, "function")
            name = self._read_chat_field(call, "name") or self._read_chat_field(fn_payload, "name")
            args_raw = (
                self._read_chat_field(call, "arguments")
                or self._read_chat_field(fn_payload, "arguments")
                or "{}"
            )
            call_id = self._read_chat_field(call, "id")
            if not name:
                continue
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                args = {}

            normalized_tool_calls.append(
                {
                    "name": name,
                    "args": args,
                    "id": call_id,
                }
            )
        return normalized_tool_calls

    def extract_usage(self, response) -> Optional[Dict[str, Any]]:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None

        if isinstance(usage, dict):
            raw = usage
        else:
            raw = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
                "cached_tokens": getattr(usage, "cached_tokens", None),
                "reasoning_tokens": getattr(usage, "reasoning_tokens", None),
                "input_tokens_details": getattr(usage, "input_tokens_details", None),
                "output_tokens_details": getattr(usage, "output_tokens_details", None),
            }

        prompt_tokens = raw.get("prompt_tokens", raw.get("input_tokens"))
        completion_tokens = raw.get("completion_tokens", raw.get("output_tokens"))
        total_tokens = raw.get("total_tokens")
        if total_tokens is None and isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        usage_out = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        if raw.get("cached_tokens") is not None:
            usage_out["cached_tokens"] = raw.get("cached_tokens")
        if raw.get("reasoning_tokens") is not None:
            usage_out["reasoning_tokens"] = raw.get("reasoning_tokens")
        if raw.get("input_tokens_details") is not None:
            usage_out["input_tokens_details"] = raw.get("input_tokens_details")
        if raw.get("output_tokens_details") is not None:
            usage_out["output_tokens_details"] = raw.get("output_tokens_details")

        if not any(isinstance(val, (int, float)) for val in usage_out.values()):
            return None
        return usage_out


class AzureOpenAIProvider(OpenAIProvider):
    name = "azure_openai"

    def __init__(self, api_key: Optional[str], model: str, base_url: str, api_version: str):
        super().__init__(api_key=api_key, model=model, base_url=base_url)
        try:
            from openai import AzureOpenAI
        except ImportError as exc:
            raise ProviderError("openai SDK not available") from exc
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=base_url,
            api_version=api_version,
        )
        self.base_url = str(base_url or "").strip().rstrip("/") or None
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
        self.base_url = str(base_url).strip().rstrip("/") if base_url else None
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.model = model

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        return {"system": system_instruction, "messages": [], "tools": tools}

    def _format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for tool in (tools or []):
            if not isinstance(tool, dict):
                continue

            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue

            formatted.append(
                {
                    "name": name,
                    "description": tool.get("description"),
                    "input_schema": tool.get("parameters") or {"type": "object", "properties": {}},
                }
            )

        return formatted

    def _response_content_blocks(self, response) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        for part in (getattr(response, "content", None) or []):
            part_type = getattr(part, "type", None)
            if part_type == "text":
                blocks.append({"type": "text", "text": getattr(part, "text", "") or ""})
                continue
            if part_type == "tool_use":
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": getattr(part, "id", None),
                        "name": getattr(part, "name", None),
                        "input": getattr(part, "input", None) or {},
                    }
                )
                continue

            # Preserve future Anthropic content block types when available.
            if hasattr(part, "model_dump"):
                dumped = part.model_dump(exclude_none=True)
                if isinstance(dumped, dict) and dumped.get("type"):
                    blocks.append(dumped)
        return blocks

    def _append_assistant_response(self, session, response) -> None:
        content_blocks = self._response_content_blocks(response)
        if content_blocks:
            session["messages"].append({"role": "assistant", "content": content_blocks})

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        try:
            response = self.client.messages.create(
                model=self.model,
                system=session["system"],
                messages=session["messages"],
                tools=self._format_tools(session.get("tools", [])),
                temperature=self.temperature,
                max_tokens=self.max_tokens or 512,
            )
        except Exception as exc:
            self._raise_provider_error(exc, "Anthropic", endpoint_url=self.base_url)
            raise
        self._append_assistant_response(session, response)
        return response

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        if not isinstance(tool_result, str):
            tool_result = json.dumps(tool_result)
        if not tool_call_id:
            raise ProviderError("Anthropic tool_result requires a tool_call_id")
        session["messages"].append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": [
                            {
                                "type": "text",
                                "text": tool_result,
                            }
                        ],
                    }
                ],
            }
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                system=session["system"],
                messages=session["messages"],
                tools=self._format_tools(session.get("tools", [])),
                temperature=self.temperature,
                max_tokens=self.max_tokens or 512,
            )
        except Exception as exc:
            self._raise_provider_error(exc, "Anthropic", endpoint_url=self.base_url)
            raise
        self._append_assistant_response(session, response)
        return response

    def extract_text(self, response) -> str:
        parts = response.content or []
        texts = [p.text for p in parts if getattr(p, "type", None) == "text"]
        return "".join(texts).strip()

    def extract_usage(self, response) -> Optional[Dict[str, Any]]:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return None

        if isinstance(usage, dict):
            prompt_tokens = usage.get("input_tokens")
            completion_tokens = usage.get("output_tokens")
        else:
            prompt_tokens = getattr(usage, "input_tokens", None)
            completion_tokens = getattr(usage, "output_tokens", None)

        if prompt_tokens is None and completion_tokens is None:
            return None

        total_tokens = None
        if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        parts = response.content or []
        if not parts:
            return []
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


class GeminiProvider(BaseProvider):
    name = "gemini"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str):
        super().__init__()
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderError("google-genai not available") from exc
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is required for gemini")
        self.client = genai.Client(api_key=api_key)
        self.types = types
        self.model_name = model

    def _to_schema_type(self, json_type: Optional[str]):
        if json_type == "integer":
            return self.types.Type.INTEGER
        if json_type == "number":
            return self.types.Type.NUMBER
        if json_type == "boolean":
            return self.types.Type.BOOLEAN
        if json_type == "array":
            return self.types.Type.ARRAY
        if json_type == "object":
            return self.types.Type.OBJECT
        return self.types.Type.STRING

    def _build_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_type = schema.get("type") or "object"
        if schema_type == "array":
            items = schema.get("items") or {}
            return {
                "type": "array",
                "items": self._build_schema(items),
                "description": schema.get("description", ""),
            }
        if schema_type == "object":
            properties = {
                key: self._build_schema(val or {})
                for key, val in (schema.get("properties") or {}).items()
            }
            return {
                "type": "object",
                "properties": properties,
                "required": schema.get("required") or [],
                "description": schema.get("description", ""),
            }
        return {
            "type": schema_type,
            "description": schema.get("description", ""),
        }

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        tool_decls = []
        for tool in tools:
            schema = self._build_schema(tool.get("parameters") or {"type": "object"})
            tool_decls.append(
                self.types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description") or "",
                    parameters_json_schema=schema,
                )
            )
        tools_config = (
            [self.types.Tool(function_declarations=tool_decls)] if tool_decls else None
        )
        config_kwargs = {
            "system_instruction": system_instruction,
            "temperature": self.temperature,
        }
        if tools_config:
            config_kwargs["tools"] = tools_config
            config_kwargs["tool_config"] = self.types.ToolConfig(
                function_calling_config=self.types.FunctionCallingConfig(mode="AUTO")
            )
        config = self.types.GenerateContentConfig(**config_kwargs)
        chat = self.client.chats.create(model=self.model_name, config=config)
        return {"chat": chat}

    def send_user_message(self, session, content: str):
        try:
            return session["chat"].send_message(content)
        except Exception as exc:
            self._raise_provider_error(exc, "Gemini")
            raise

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        try:
            parsed_result = json.loads(tool_result)
        except Exception:
            parsed_result = {"result": tool_result}
        if not isinstance(parsed_result, dict):
            parsed_result = {"result": parsed_result}
        try:
            return session["chat"].send_message(
                [
                    self.types.Part(
                        function_response=self.types.FunctionResponse(
                            name=tool_name,
                            response=parsed_result,
                        )
                    )
                ]
            )
        except Exception as exc:
            self._raise_provider_error(exc, "Gemini")
            raise

    def extract_text(self, response) -> str:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        parts_text: List[str] = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    parts_text.append(str(part_text))
        return "".join(parts_text).strip()

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return []
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None)
        if not parts:
            return []
        tool_calls: List[Dict[str, Any]] = []
        for part in parts:
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

    def extract_usage(self, response) -> Optional[Dict[str, Any]]:
        usage = getattr(response, "usage_metadata", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage_metadata") or response.get("usageMetadata")
        if usage is None:
            return None

        if isinstance(usage, dict):
            raw = usage
        else:
            raw = {
                "prompt_token_count": getattr(usage, "prompt_token_count", None),
                "response_token_count": getattr(usage, "response_token_count", None),
                "total_token_count": getattr(usage, "total_token_count", None),
                "cached_content_token_count": getattr(usage, "cached_content_token_count", None),
                "thoughts_token_count": getattr(usage, "thoughts_token_count", None),
                "prompt_tokens_details": getattr(usage, "prompt_tokens_details", None),
                "response_tokens_details": getattr(usage, "response_tokens_details", None),
            }

        prompt_tokens = raw.get("prompt_token_count")
        completion_tokens = raw.get("response_token_count")
        total_tokens = raw.get("total_token_count")
        if total_tokens is None and isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            total_tokens = prompt_tokens + completion_tokens

        usage_out = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        if raw.get("cached_content_token_count") is not None:
            usage_out["cached_tokens"] = raw.get("cached_content_token_count")
        if raw.get("thoughts_token_count") is not None:
            usage_out["reasoning_tokens"] = raw.get("thoughts_token_count")
        if raw.get("prompt_tokens_details") is not None:
            usage_out["prompt_tokens_details"] = raw.get("prompt_tokens_details")
        if raw.get("response_tokens_details") is not None:
            usage_out["response_tokens_details"] = raw.get("response_tokens_details")

        if not any(isinstance(val, (int, float)) for val in usage_out.values()):
            return None
        return usage_out


class HuggingFaceProvider(BaseProvider):
    name = "huggingface"
    supports_tools = True

    def __init__(self, api_key: Optional[str], model: str, base_url: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        normalized_base_url = str(base_url).strip() if base_url is not None else ""
        self.base_url = normalized_base_url.rstrip("/") if normalized_base_url else None
        self.timeout = max(self.timeout, 90)

        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise ProviderError("huggingface_hub SDK not available") from exc

        if self.base_url:
            self.client = InferenceClient(
                base_url=self.base_url,
                token=self.api_key,
                timeout=self.timeout,
            )
        else:
            self.client = InferenceClient(
                model=self.model,
                token=self.api_key,
                timeout=self.timeout,
            )

        self._tools: List[Dict[str, Any]] = []

    def start_chat(self, system_instruction: str, tools: List[Dict[str, Any]]):
        self._tools = self._format_tools(tools)
        return {"system": system_instruction, "history": []}

    def _format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for tool in (tools or []):
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if not isinstance(name, str) or not name.strip():
                continue

            function_payload: Dict[str, Any] = {
                "name": name,
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
            }
            description = tool.get("description")
            if isinstance(description, str) and description.strip():
                function_payload["description"] = description

            formatted.append({"type": "function", "function": function_payload})
        return formatted

    def _create_completion(self, messages: List[Dict[str, Any]]):
        kwargs: Dict[str, Any] = {
            "messages": messages,
            "temperature": self.temperature,
        }
        kwargs.pop("timeout", None)
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        if self._tools:
            kwargs["tools"] = self._tools
            kwargs["tool_choice"] = "auto"

        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            status_code = self._extract_status_code(exc)
            if status_code == 400 and self._tools:
                logger.warning("HuggingFace tools rejected; retrying without tools: %s", exc)
                fallback_kwargs = dict(kwargs)
                fallback_kwargs.pop("tools", None)
                fallback_kwargs.pop("tool_choice", None)
                try:
                    return self.client.chat.completions.create(**fallback_kwargs)
                except Exception as fallback_exc:
                    self._raise_provider_error(
                        fallback_exc,
                        "HuggingFace",
                        endpoint_url=self.base_url,
                    )
                    raise

            self._raise_provider_error(exc, "HuggingFace", endpoint_url=self.base_url)
            raise

    def send_user_message(self, session, content: str):
        session["history"].append({"role": "user", "content": content})
        messages = [{"role": "system", "content": session["system"]}, *session["history"]]
        response = self._create_completion(messages)

        assistant_text = self.extract_text(response)
        if not assistant_text.strip():
            assistant_text = (
                "The model is taking longer than expected to load on the free tier. "
                "Please try again in a few seconds."
            )
        session["history"].append({"role": "assistant", "content": assistant_text})
        return response

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        if not isinstance(tool_result, str):
            tool_result = json.dumps(tool_result)
        session["history"].append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": tool_result,
            }
        )
        messages = [{"role": "system", "content": session["system"]}, *session["history"]]
        response = self._create_completion(messages)

        assistant_text = self.extract_text(response)
        if not assistant_text.strip():
            assistant_text = (
                "The model is taking longer than expected to load on the free tier. "
                "Please try again in a few seconds."
            )
        session["history"].append({"role": "assistant", "content": assistant_text})
        return response

    def extract_text(self, response) -> str:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                content = message.get("content")
                return content or ""
            return ""

        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) if message else None
        return content or ""

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if not choices:
                return []
            message = choices[0].get("message") or {}
            tool_calls = message.get("tool_calls") or []
            return list(tool_calls)

        choices = getattr(response, "choices", None) or []
        if not choices:
            return []
        message = getattr(choices[0], "message", None)
        tool_calls = getattr(message, "tool_calls", None) or []
        return list(tool_calls)


def select_provider(
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    mode_override: Optional[str] = None,
) -> BaseProvider:
    mode = (mode_override or settings.LIBRARIAN_MODE).lower()
    provider = (provider_override or settings.LLM_PROVIDER).lower()
    model = model_override or settings.LLM_MODEL

    if mode == "open_source":
        if provider in {"openai_compatible", "vllm", "tgi", "lmstudio", "ollama"}:
            return get_llm_provider(
                provider_name=provider,
                model_id=model,
                api_key=os.getenv("OPENAI_API_KEY"),
            )

    return get_llm_provider(provider_name=provider, model_id=model)


def _require_api_key(provider_label: str, configured_api_key: Optional[str] = None) -> str:
    value = str(configured_api_key or "").strip()
    if value:
        return value

    env_key = f"{provider_label.upper()}_API_KEY"
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    raise ProviderError(f"Missing API key for provider '{provider_label}'. Set {env_key} in .env")


def _looks_local_openai_endpoint(base_url: Optional[str]) -> bool:
    endpoint = str(base_url or "").strip().lower()
    if not endpoint:
        return False
    return (
        "localhost" in endpoint
        or "127.0.0.1" in endpoint
        or "host.docker.internal" in endpoint
    )


def get_llm_provider(provider_name: str, model_id: str, api_key: Optional[str] = None) -> BaseProvider:
    """Create a provider instance from explicit provider/model settings."""
    provider = (provider_name or "").strip().lower()
    model = str(model_id or "").strip()
    if not model:
        raise ValueError("model_id is required")

    if provider in {"openai", "openai_compatible", "vllm", "tgi", "lmstudio", "ollama"}:
        base_url = settings.OPENAI_BASE_URL or settings.LLM_BASE_URL
        if provider == "ollama" and not base_url:
            base_url = "http://localhost:11434/v1"

        resolved_api_key = str(api_key or "").strip() or (os.getenv("OPENAI_API_KEY") or "").strip()
        if not resolved_api_key and _looks_local_openai_endpoint(base_url):
            resolved_api_key = "ollama"

        if provider == "openai" and not resolved_api_key:
            resolved_api_key = _require_api_key("openai", api_key)

        return OpenAIProvider(api_key=resolved_api_key or None, model=model, base_url=base_url)

    if provider == "gemini":
        resolved_api_key = _require_api_key("gemini", api_key)
        return GeminiProvider(api_key=resolved_api_key, model=model)

    if provider == "anthropic":
        resolved_api_key = _require_api_key("anthropic", api_key)
        base_url = os.getenv("ANTHROPIC_BASE_URL") or settings.LLM_BASE_URL
        return AnthropicProvider(api_key=resolved_api_key, model=model, base_url=base_url)

    if provider in {"huggingface", "hf"}:
        resolved_api_key = _require_api_key("huggingface", api_key)
        base_url = settings.HUGGINGFACE_BASE_URL
        return HuggingFaceProvider(api_key=resolved_api_key, model=model, base_url=base_url)

    raise ValueError(
        "Unknown provider "
        f"'{provider_name}'. Supported providers: openai, gemini, anthropic, huggingface "
        "(aliases: openai_compatible, vllm, tgi, lmstudio, ollama)"
    )


def is_provider_available() -> bool:
    try:
        select_provider()
        return True
    except Exception as exc:
        logger.warning("Provider unavailable: %s", exc)
        return False
