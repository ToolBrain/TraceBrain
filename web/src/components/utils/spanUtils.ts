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
  return type === "llm_inference"
    ? span?.attributes["tracebrain.llm.completion"]
    : span?.attributes["tracebrain.tool.output"];
}

export function spanGetSystemPrompt(span: Span) {
  return span?.attributes["system_prompt"];
}
