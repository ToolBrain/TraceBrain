# Trace Reconstruction Guide

This guide explains how to reconstruct full prompt context from TraceBrain delta-based OTLP traces. It is designed for users preparing training data (SFT, RL, DPO) from storage-efficient traces.

## 1. Introduction

TraceBrain stores traces in a **delta-based OTLP schema**. Each span only contains the **new content introduced at that step** (for example, `tracebrain.llm.new_content`), rather than the full prompt history. This design is compact and efficient for storage and analytics, but training pipelines typically require the **full context**.

**Trace Reconstruction** bridges this gap by rebuilding the complete conversation context from the deltas.

## 2. Core Reconstruction Logic

The reconstruction algorithm is a **backwards traversal** over the `parent_id` chain of `llm_inference` spans.

### Backwards Traversal Algorithm

1. Start at a specific `llm_inference` span (often the final answer).
2. Follow each `parent_id` pointer back to the root span, collecting only `llm_inference` spans.
3. Reverse the collected spans to restore chronological order.
4. Initialize the history with the top-level `system_prompt` from `trace.attributes.system_prompt`.
5. For each `llm_inference` span in order:
    - Append `tracebrain.llm.new_content` to the history.
    - If the span is **not** the target span, append the assistant `completion` from the span.

### Why This Works

Each `llm_inference` span stores the delta for that step. The `parent_id` chain preserves the causal ordering of those steps. Adding `new_content` plus the intermediate `completion` preserves conversation continuity without duplicating tool output.

### ASCII Diagram

```
[Span D*] <- parent_id <- [Span C] <- parent_id <- [Span B] <- parent_id <- [Span A]
     |                         |                         |                  |
     |                         |                         |                  |
 new_content + completion   new_content + completion   new_content + completion
 (only if not target)       (only if not target)       (only if not target)

*Span D is the target span: append new_content only (no completion).
```

## 3. Standard SDK Views

The SDK provides built-in reconstruction helpers in `TraceScope`:

| Method | Output | Use Case |
| --- | --- | --- |
| `TraceScope.to_messages(trace_data)` | ChatML list of `{role, content}` | SFT, ICL, evaluation |
| `TraceScope.to_turns(trace_data)` | Structured turns (TraceBrain 1.0 style) | RL, tool-augmented training |
| `TraceScope.to_tracebrain_turns(trace_data)` | TraceBrain 1.0 compatible turns | Backward-compatible pipelines |

These helpers handle the backwards traversal and ordering for you.

## 4. Code Examples

### Reconstructing Messages and Turns

```python
from tracebrain.sdk.client import TraceClient, TraceScope

client = TraceClient(base_url="http://localhost:8000")
trace_data = client.get_trace("trace_id_123")

# Exporting for SFT (ChatML-style messages)
messages = TraceScope.to_messages(trace_data)

# Exporting for TraceBrain 1.0 RL (structured turns)
turns = TraceScope.to_turns(trace_data)
```

### Export and Parse JSONL for Training

```python
import json
from tracebrain.sdk.client import TraceClient, TraceScope

client = TraceClient(base_url="http://localhost:8000")
jsonl_payload = client.export_traces(min_rating=4, limit=100)

# Each line is a full OTLP trace payload
traces = [json.loads(line) for line in jsonl_payload.splitlines() if line.strip()]

messages_per_trace = [TraceScope.to_messages(t) for t in traces]
```

## 5. Building a Custom Reconstructor

Advanced users may need a custom reconstruction format (for example, DPO pairs or task-specific structures). You can implement your own logic directly from the raw OTLP data:

- `trace_data["attributes"]["system_prompt"]`
- `span["attributes"]["tracebrain.llm.new_content"]`
- `span["attributes"]["tracebrain.llm.completion"]`
- `span["parent_id"]`

### Minimal Pseudocode

```
path = []
current = target_span
while current is not None:
    if span_type == "llm_inference":
        path.insert(0, current)
    current = span_parent_id

history = [system_prompt]
for span in path:
    history.extend(parse(span.new_content))
    if span != target_span:
        history.append({"role": "assistant", "content": span.completion})
```

This is the same logic used by the SDK helpers, but you can adapt it to custom formats or target datasets.

---

If you want a ready-to-run reconstructor script for your pipeline, open an issue or request an example tailored to your format (SFT, RL, DPO, or evaluation).