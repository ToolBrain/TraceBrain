import type { Trace } from "../../types/trace";

export function traceGetEpisodeId(trace: Trace) {
  return trace?.attributes["tracebrain.episode.id"];
}

export function traceGetStatus(trace: Trace) {
  return trace?.attributes["tracebrain.trace.status"];
}

export function traceGetPriority(trace: Trace) {
  return trace?.attributes["tracebrain.trace.priority"];
}

export function traceGetEvaluation(trace: Trace) {
  return trace?.attributes["tracebrain.trace.ai_evaluation"];
}
