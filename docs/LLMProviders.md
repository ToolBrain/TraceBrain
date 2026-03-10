# LLM Provider Guide

This guide explains how to use TraceBrain's LLM providers in external agents and how to attach usage metadata to spans.

## 1. What the LLM Providers Are

TraceBrain ships a lightweight provider layer in `tracebrain.core.llm_providers` that wraps:
- OpenAI
- Azure OpenAI
- Anthropic
- Gemini
- OpenAI-compatible endpoints

These providers are used internally (Librarian/Judge/Curator), but you can also import them in your own agent code.

## 2. Quick Start (External Agent)

```python
from tracebrain.core.llm_providers import select_provider
from tracebrain.sdk.client import TraceScope
from tracebrain.core.schema import TraceBrainAttributes, SpanType

provider = select_provider(provider_override="openai", model_override="gpt-4o-mini")
session = provider.start_chat("You are a helpful assistant.", tools=[])

response = provider.send_user_message(session, "Hello!")
content = provider.extract_text(response)

span = {
    "span_id": "...",
    "parent_id": None,
    "name": "LLM Inference",
    "start_time": "2026-03-10T10:00:00Z",
    "end_time": "2026-03-10T10:00:01Z",
    "attributes": {
        TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
        TraceBrainAttributes.LLM_NEW_CONTENT: "[{\"role\": \"user\", \"content\": \"Hello!\"}]",
        TraceBrainAttributes.LLM_COMPLETION: content,
    },
}

# Attach usage to the span (if response includes usage metadata)
TraceScope.attach_usage(span, response, provider="openai")
```

## 3. Usage Metadata Helpers

TraceBrain exposes two helpers to make usage attachment consistent:

- `extract_usage_from_response(provider, response)`
  - Returns a normalized dict with `prompt_tokens`, `completion_tokens`, `total_tokens`.
- `TraceScope.attach_usage(span, response, provider=None)`
  - Writes `tracebrain.usage` into a span.
  - If `provider` is omitted, it falls back to `settings.LLM_PROVIDER`.

Normalized `tracebrain.usage` format:

```json
{
  "prompt_tokens": 350,
  "completion_tokens": 240,
  "total_tokens": 590
}
```

Extra fields (when available) may be included:
- `cached_tokens`
- `reasoning_tokens`
- `input_tokens_details`
- `output_tokens_details`

## 4. Provider Mapping Notes

- OpenAI and OpenAI-compatible providers expose `usage` with `input_tokens`, `output_tokens`, `total_tokens`.
- Anthropic exposes `usage` with `input_tokens`, `output_tokens`.
- Gemini exposes `usage_metadata` with `prompt_token_count`, `response_token_count`, `total_token_count`.

TraceBrain normalizes all of these into the same `tracebrain.usage` shape.

## 5. When You Do NOT Use TraceBrain Providers

If your agent calls model SDKs directly (for example, LangChain or a custom wrapper), TraceBrain does not see the raw response.
In that case, you must capture usage in your agent and attach it to spans manually.

Recommended pattern:

```python
from tracebrain.core.llm_providers import extract_usage_from_response

usage = extract_usage_from_response("gemini", response)
if usage:
    span["attributes"]["tracebrain.usage"] = usage
```

## 6. Common Pitfalls

- No usage data: Some providers or SDK layers do not return usage in the response. In that case, `tracebrain.usage` will be missing.
- SDK mismatch: Ensure the provider string matches `openai`, `azure_openai`, `anthropic`, `gemini`, or `openai_compatible`.
- Double counting: Only attach usage once per LLM inference span.
