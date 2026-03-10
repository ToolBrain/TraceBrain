"""Shared LLM provider selection and implementations."""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import logging
import json

import requests

from tracebrain.config import settings

logger = logging.getLogger(__name__)


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
        return {"system": system_instruction, "messages": [], "tools": tools}

    def _send_response(self, session):
        response = self.client.responses.create(
            model=self.model,
            instructions=session.get("system"),
            input=session["messages"],
            tools=[{"type": "function", "function": tool} for tool in session.get("tools", [])],
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text:
            session["messages"].append({"role": "assistant", "content": output_text})
        return response

    def send_user_message(self, session, content: str):
        session["messages"].append({"role": "user", "content": content})
        return self._send_response(session)

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        tool_message = {
            "role": "tool",
            "name": tool_name,
            "content": tool_result,
        }
        if tool_call_id:
            tool_message["tool_call_id"] = tool_call_id
        session["messages"].append(tool_message)
        return self._send_response(session)

    def extract_text(self, response) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            return output_text
        return ""

    def extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        output_items = getattr(response, "output", None) or []
        result: List[Dict[str, Any]] = []
        for item in output_items:
            item_type = getattr(item, "type", None) or item.get("type")
            if item_type not in {"tool_call", "function_call"}:
                continue
            name = getattr(item, "name", None) or item.get("name")
            args_raw = (
                getattr(item, "arguments", None)
                or item.get("arguments")
                or getattr(item, "args", None)
                or item.get("args")
                or "{}"
            )
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw)
            except json.JSONDecodeError:
                args = {}
            result.append(
                {
                    "name": name,
                    "args": args,
                    "id": getattr(item, "id", None) or item.get("id"),
                }
            )
        return result

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
        if not isinstance(tool_result, str):
            tool_result = json.dumps(tool_result)
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
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderError("google-genai not available") from exc
        if not api_key:
            raise ProviderError("LLM_API_KEY is required for gemini")
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
        return session["chat"].send_message(content)

    def send_tool_result(self, session, tool_name: str, tool_result: str, tool_call_id: Optional[str]):
        try:
            parsed_result = json.loads(tool_result)
        except Exception:
            parsed_result = {"result": tool_result}
        if not isinstance(parsed_result, dict):
            parsed_result = {"result": parsed_result}
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


def select_provider(
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    mode_override: Optional[str] = None,
) -> BaseProvider:
    mode = (mode_override or settings.LIBRARIAN_MODE).lower()
    provider = (provider_override or settings.LLM_PROVIDER).lower()
    model = model_override or settings.LLM_MODEL
    api_key = settings.LLM_API_KEY

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


def is_provider_available() -> bool:
    try:
        select_provider()
        return True
    except Exception as exc:
        logger.warning("Provider unavailable: %s", exc)
        return False
