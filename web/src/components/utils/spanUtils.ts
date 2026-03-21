import type { Span, Trace } from "../../types/trace";

export function spanGetType(span: Span) {
  return span?.attributes["tracebrain.span.type"];
}

export function spanGetToolName(span: Span) {
  return span?.attributes["tracebrain.tool.name"];
}

export function spanHasError(span: Span) {
  return span?.attributes["otel.status_code"] === "ERROR";
}

export function spanGetErrorDescription(span: Span) {
  return span?.attributes["otel.status_description"];
}

export function spanGetThought(span: Span) {
  return span?.attributes["tracebrain.llm.thought"];
}

export function spanGetToolCode(span: Span) {
  return span?.attributes["tracebrain.llm.tool_code"];
}

export function spanGetDuration(span: Span) {
  return (
    (new Date(span.end_time).getTime() - new Date(span.start_time).getTime()) /
    1000
  ).toFixed(2);
}

export function spanGetUsage(span: Span) {
  const usage = span?.attributes["tracebrain.usage"];
  if (!usage || typeof usage !== "object") {
    return null;
  }
  const values = [
    usage.prompt_tokens,
    usage.completion_tokens,
    usage.total_tokens,
  ];
  const hasNumber = values.some((val) => typeof val === "number" && !Number.isNaN(val));
  return hasNumber ? usage : null;
}

export function spanGetInput(span: Span) {
  const type = spanGetType(span);
  const value =
    type === "llm_inference"
      ? span?.attributes["tracebrain.llm.new_content"]
      : span?.attributes["tracebrain.tool.input"];
  if (value === null || value === undefined) {
    return value;
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function spanGetOutput(span: Span) {
  const type = spanGetType(span);
  const value =
    type === "llm_inference"
      ? span?.attributes["tracebrain.llm.final_answer"]
      : span?.attributes["tracebrain.tool.output"];
  if (value === null || value === undefined) {
    return value;
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function spanGetSystemPrompt(span: Span | null | undefined, trace?: Trace | null) {
  return span?.attributes["system_prompt"] ?? trace?.attributes?.["system_prompt"];
}
