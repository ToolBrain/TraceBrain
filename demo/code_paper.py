
def convert_smolagent_to_otlp(agent: CodeAgent) -> Dict:
    """Core logic mapping SmolAgents memory steps to TraceBrain OTLP."""
    spans = []
    parent_id = None
    
    for step in agent.memory.steps:
        if not isinstance(step, ActionStep): continue

        # 1. Create LLM Inference Span
        llm_span_id = uuid.uuid4().hex[:16]
        # Only store the delta (new messages) for this turn
        new_content = [msg.model_dump() for msg in step.model_input_messages]
        
        spans.append({
            "span_id": llm_span_id, "parent_id": parent_id,
            "name": "LLM Inference",
            "attributes": {
                "tracebrain.span.type": "llm_inference",
                "tracebrain.llm.new_content": json.dumps(new_content),
                "tracebrain.llm.completion": step.model_output,
                "tracebrain.llm.tool_code": step.code_action
            }
        })
        parent_id = llm_span_id

        # 2. Create Tool Execution Span (if tool called)
        if step.code_action:
            tool_span_id = uuid.uuid4().hex[:16]
            spans.append({
                "span_id": tool_span_id, "parent_id": parent_id,
                "name": f"Tool Execution",
                "attributes": {
                    "tracebrain.span.type": "tool_execution",
                    "tracebrain.tool.input": step.code_action,
                    "tracebrain.tool.output": step.observations,
                }
            })
            parent_id = tool_span_id

    return {"trace_id": uuid.uuid4().hex, "spans": spans}

def convert_langchain_to_otlp(messages: list) -> Dict:
    """Core logic mapping LangChain Message objects to OTLP Spans."""
    spans = []; parent_id = None

    for msg in messages:
        span_id = uuid.uuid4().hex[:16]
        
        if msg.type == "human":
            # Map User Input -> LLM Inference Span
            spans.append({
                "span_id": span_id, "parent_id": parent_id,
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.new_content": json.dumps([{"role": "user", "content": msg.content}])
                }
            })
            
        elif msg.type == "ai":
            # Map AI Response -> LLM Inference Span
            spans.append({
                "span_id": span_id, "parent_id": parent_id,
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.completion": msg.content,
                    "tracebrain.llm.tool_code": str(msg.tool_calls)
                }
            })
            
        elif msg.type == "tool":
            # Map Tool Output -> Tool Execution Span
            spans.append({
                "span_id": span_id, "parent_id": parent_id,
                "attributes": {
                    "tracebrain.span.type": "tool_execution",
                    "tracebrain.tool.name": msg.name,
                    "tracebrain.tool.output": msg.content
                }
            })
        
        parent_id = span_id # Chain spans sequentially

    return {"trace_id": uuid.uuid4().hex, "spans": spans}
