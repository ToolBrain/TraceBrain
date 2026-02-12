# Trace Reconstruction Guide

This guide explains how to reconstruct full prompt context from TraceBrain delta-based OTLP traces. It is designed for users preparing training data (SFT, RL, DPO) from storage-efficient traces.

## 1. Introduction

TraceBrain stores traces in a **delta-based OTLP schema**. Each span only contains the **new content introduced at that step** (for example, `tracebrain.llm.new_content`), rather than the full prompt history. This design is compact and efficient for storage and analytics, but training pipelines typically require the **full context**.

**Trace Reconstruction** bridges this gap by rebuilding the complete conversation context from the deltas.

## 2. Core Reconstruction Logic

The reconstruction algorithm is a **backwards traversal** over the `parent_id` chain.

### Backwards Traversal Algorithm

1. Start at a specific span (often the last LLM step or final answer).
2. Follow each `parent_id` pointer back to the root span.
3. Collect:
   - `tracebrain.llm.new_content` from LLM spans
   - `tracebrain.tool.output` from tool execution spans
4. Reverse the collected items to restore chronological order.
5. Prepend the top-level `system_prompt` from `trace.attributes.system_prompt`.

### Why This Works

Each span stores only the delta for that step. The `parent_id` chain preserves the causal ordering of steps. Traversing backwards and reversing the list reconstructs the full, ordered prompt.

### ASCII Diagram

```
[Span D] <- parent_id <- [Span C] <- parent_id <- [Span B] <- parent_id <- [Span A]
   |                         |                         |                  |
   |                         |                         |                  |
 new_content/tool_output collected in reverse, then reversed to chronological order
```

## 3. Standard SDK Views

The SDK provides built-in reconstruction helpers in `TraceClient`:

| Method | Output | Use Case |
| --- | --- | --- |
| `TraceClient.to_messages(trace_data)` | ChatML list of `{role, content}` | SFT, ICL, evaluation |
| `TraceClient.to_turns(trace_data)` | Structured turns (TraceBrain 1.0 style) | RL, tool-augmented training |
| `TraceClient.to_tracebrain_turns(trace_data)` | TraceBrain 1.0 compatible turns | Backward-compatible pipelines |

These helpers handle the backwards traversal and ordering for you.

## 4. Code Examples

### Reconstructing Messages and Turns

```python
from tracebrain.sdk.client import TraceClient

client = TraceClient(base_url="http://localhost:8000")
trace_data = client.get_trace("trace_id_123")

# Exporting for SFT (ChatML-style messages)
messages = TraceClient.to_messages(trace_data)

# Exporting for TraceBrain 1.0 RL (structured turns)
turns = TraceClient.to_turns(trace_data)
```

### Export and Parse JSONL for Training

```python
import json
from tracebrain.sdk.client import TraceClient

client = TraceClient(base_url="http://localhost:8000")
jsonl_payload = client.export_traces(min_rating=4, limit=100)

# Each line is a full OTLP trace payload
traces = [json.loads(line) for line in jsonl_payload.splitlines() if line.strip()]

messages_per_trace = [TraceClient.to_messages(t) for t in traces]
```

## 5. Building a Custom Reconstructor

Advanced users may need a custom reconstruction format (for example, DPO pairs or task-specific structures). You can implement your own logic directly from the raw OTLP data:

- `trace_data["attributes"]["system_prompt"]`
- `span["attributes"]["tracebrain.llm.new_content"]`
- `span["attributes"]["tracebrain.tool.output"]`
- `span["parent_id"]`

### Minimal Pseudocode

```
collect = []
current = last_span
while current is not None:
    if span_type == "llm_inference":
        collect.append(llm_new_content)
    if span_type == "tool_execution":
        collect.append(tool_output)
    current = span_parent_id

collect.reverse()
full_context = [system_prompt] + collect
```

This is the same logic used by the SDK helpers, but you can adapt it to custom formats or target datasets.

---

If you want a ready-to-run reconstructor script for your pipeline, open an issue or request an example tailored to your format (SFT, RL, DPO, or evaluation).