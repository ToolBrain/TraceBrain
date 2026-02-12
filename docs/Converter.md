# Building Your Own Trace Converter

This guide explains the TraceBrain OTLP schema and shows how to build a custom converter for your own agent.

## 1. The Standard Schema (OTLP)

A trace represents a single, complete agent execution. It stores the system prompt once and then stores each step as a span. This design is storage-efficient and makes it easy to rebuild the full conversation later.

### Trace structure

```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "attributes": {
    "system_prompt": "You are a helpful assistant that must use tools.",
    "tracebrain.episode.id": "ep-8f2a1c9b"
  },
  "spans": [
    { "...": "span 1" },
    { "...": "span 2" },
    { "...": "span 3" }
  ]
}
```

**Fields**
- `trace_id`: A unique 32-character hex string for the entire execution.
- `attributes`: Trace-level metadata. At minimum, store `system_prompt` once here.
- `spans`: An ordered list of spans (steps) that form a causal chain.

### Episode grouping (`tracebrain.episode.id`)

TraceBrain adds `tracebrain.episode.id` to group multiple attempts of the same task into a single episode. This is not part of standard OpenTelemetry, but it is critical for Agentic AI workflows where one task may have several retries.

Add it at the trace level:

```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "attributes": {
    "system_prompt": "You are a helpful assistant that must use tools.",
    "tracebrain.episode.id": "ep-8f2a1c9b"
  },
  "spans": [
    { "...": "span 1" }
  ]
}
```

How to choose `tracebrain.episode.id`:
- Prefer a stable ID from your app (session_id, conversation_id, task_id).
- If you do not have one, generate it once per task and reuse it across retries.

### Span structure (common fields)

```json
{
  "span_id": "00f067aa0ba902b7",
  "parent_id": null,
  "name": "LLM Inference (Tool Call)",
  "start_time": "2025-10-27T10:30:01.123Z",
  "end_time": "2025-10-27T10:30:02.234Z",
  "attributes": {
    "tracebrain.span.type": "llm_inference",
    "tracebrain.llm.new_content": "[{\"role\": \"user\", \"content\": \"What is the weather in Tokyo?\"}]",
    "tracebrain.llm.completion": "{\"tool_call\": {\"name\": \"get_weather\", \"arguments\": {\"location\": \"Tokyo\"}}}",
    "tracebrain.llm.thought": null,
    "tracebrain.llm.tool_code": "get_weather({'location': 'Tokyo'})",
    "tracebrain.llm.final_answer": null
  }
}
```

**Fields**
- `span_id`: A unique identifier for this step.
- `parent_id`: The `span_id` of the step that caused this step. This is how TraceBrain builds the chain/tree in the UI and how you reconstruct the prompt later. The first span has `parent_id = null`.
- `name`: A short human-readable name (for UI).
- `start_time` / `end_time`: Standard timing fields (ISO 8601).
- `attributes`: The schema-specific payload described below.

### Span types and custom attributes

**LLM inference span** (`tracebrain.span.type = "llm_inference"`)

```json
{
  "tracebrain.span.type": "llm_inference",
  "tracebrain.llm.new_content": "[{\"role\": \"user\", \"content\": \"What is the weather in Tokyo?\"}]",
  "tracebrain.llm.completion": "{\"tool_call\": {\"name\": \"get_weather\", \"arguments\": {\"location\": \"Tokyo\"}}}",
  "tracebrain.llm.thought": null,
  "tracebrain.llm.tool_code": "get_weather({'location': 'Tokyo'})",
  "tracebrain.llm.final_answer": null
}
```

**Meaning of key fields**
- `tracebrain.llm.new_content`: The delta for this turn. It contains only the *new messages introduced in this step*, not the full history. This is the core of the storage-efficient design.
- `tracebrain.llm.completion`: The raw model output for this step.
- `tracebrain.llm.thought`: Optional parsed reasoning text.
- `tracebrain.llm.tool_code`: The tool call string if the model decided to call a tool.
- `tracebrain.llm.final_answer`: The final response when the model is done. An LLM step should have either `tool_code` or `final_answer`, not both.

**Tool execution span** (`tracebrain.span.type = "tool_execution"`)

```json
{
  "tracebrain.span.type": "tool_execution",
  "tracebrain.tool.name": "get_weather",
  "tracebrain.tool.input": "{'location': 'Tokyo'}",
  "tracebrain.tool.output": "70F and sunny"
}
```

**Meaning of key fields**
- `tracebrain.tool.name`: Tool identifier.
- `tracebrain.tool.input`: String representation of the tool arguments.
- `tracebrain.tool.output`: String representation of the tool result.

**Why `parent_id` matters**
The delta-based schema relies on the causal chain between steps. To rebuild the full prompt for any step, you traverse backwards using `parent_id`, collecting:
- `tracebrain.llm.new_content` from LLM spans
- `tracebrain.tool.output` from tool spans

This makes the trace compact while still being fully reconstructable.

## 2. The Recipe (General Method)

Think of your agent run as a list of steps. For each step:
- If it is a reasoning/model step, create an **LLM Inference** span.
- If it is a tool call/execution step, create a **Tool Execution** span.
- Link each span to the previous one using `parent_id`.

Checklist:
- Generate `trace_id` once per run.
- Create spans in chronological order.
- Use `parent_id` to create the causal chain.
- Store only the delta in `tracebrain.llm.new_content`.
- Set `tracebrain.episode.id` to group retries of the same task.

## 3. Example Implementation (Template)

Below is a minimal converter example using a simple list of steps. Copy and adapt it to your agent objects.

```python
import uuid
from datetime import datetime, timezone


def iso_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Example input format
# steps = [
#   {"type": "llm", "new_content": [{"role": "user", "content": "Hi"}], "completion": "...", "thought": "...", "tool_code": "tool(...)"},
#   {"type": "tool", "name": "tool", "input": "{...}", "output": "result"},
#   {"type": "llm", "new_content": [{"role": "assistant", "content": "Done"}], "completion": "Done", "final_answer": "Done"}
# ]

def convert_steps_to_otlp(steps, system_prompt, episode_id=None):
    trace_id = uuid.uuid4().hex
  episode_id = episode_id or f"ep-{uuid.uuid4().hex[:8]}"
    spans = []
    parent_id = None

    for step in steps:
        span_id = uuid.uuid4().hex[:16]

        if step["type"] == "llm":
            attrs = {
                "tracebrain.span.type": "llm_inference",
                "tracebrain.llm.new_content": json.dumps(step.get("new_content", [])),
                "tracebrain.llm.completion": step.get("completion"),
                "tracebrain.llm.thought": step.get("thought"),
                "tracebrain.llm.tool_code": step.get("tool_code"),
                "tracebrain.llm.final_answer": step.get("final_answer"),
            }
            name = "LLM Inference"
        else:
            attrs = {
                "tracebrain.span.type": "tool_execution",
                "tracebrain.tool.name": step.get("name"),
                "tracebrain.tool.input": step.get("input"),
                "tracebrain.tool.output": step.get("output"),
            }
            name = f"Tool Execution: {step.get('name', 'unknown')}"

        spans.append({
            "span_id": span_id,
            "parent_id": parent_id,
            "name": name,
            "start_time": iso_now(),
            "end_time": iso_now(),
            "attributes": attrs,
        })

        parent_id = span_id

    return {
        "trace_id": trace_id,
        "attributes": {
          "system_prompt": system_prompt,
          "tracebrain.episode.id": episode_id,
        },
        "spans": spans,
    }
```

Tips:
- Keep the conversion logic isolated so it is easy to port to different agent frameworks.
- Use your agent memory to construct the `steps` list, then map each step to a span.
- Ensure the causal chain is correct via `parent_id`.
