"""Shared LLM provider selection and implementations."""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import logging
import json

import requests

from toolbrain_tracing.config import settings

logger = logging.getLogger(__name__)


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
            raise ProviderError("LLM_API_KEY is required for gemini")
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
