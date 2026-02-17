import type { Span } from "../../types/trace";

export function spanGetType(span: Span) {
  return span?.attributes["tracebrain.span.type"];
}

export function spanGetToolName(span: Span) {
  return span?.attributes["tracebrain.tool.name"];
}

export function spanHasError(span: Span) {
  return span?.attributes["otel.status_code"] === "ERROR";
}

export function spanGetUsage(span: Span) {
  return span?.attributes["tracebrain.usage"];
}

export function spanGetInput(span: Span) {
  const type = spanGetType(span);
  return type === "llm_inference"
    ? span?.attributes["tracebrain.llm.new_content"]
    : span?.attributes["tracebrain.tool.input"];
}

export function spanGetOutput(span: Span) {
  const type = spanGetType(span);
  const value =
    type === "llm_inference"
      ? span?.attributes["tracebrain.llm.completion"]
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

export const spanGetDuration = (span: Span): string => {
  const ms =
    new Date(span.end_time).getTime() - new Date(span.start_time).getTime();
  return (ms / 1000).toFixed(2);
};

export function spanGetSystemPrompt(span: Span) {
  return span?.attributes["system_prompt"];
}
