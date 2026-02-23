import type { Trace } from "../../types/trace";
import { spanGetUsage } from "./spanUtils";

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
  return trace?.attributes?.["tracebrain.ai_evaluation"];
}

export function traceGetErrorType(trace: Trace) {
  return trace?.attributes?.["tracebrain.ai_evaluation"]?.error_type ?? "none";
}

export function traceGetLatestFeedback(trace: Trace) {
  if (!trace?.feedbacks?.length) {
    return null;
  }
  return trace.feedbacks[0];
}

export const traceGetDuration = (trace: Trace): number => {
  if (!trace.spans.length) {
    return 0;
  }
  const spanTimes = trace.spans
    .map((span) => ({
      start: new Date(span.start_time).getTime(),
      end: new Date(span.end_time).getTime(),
    }))
    .filter((t) => !Number.isNaN(t.start) && !Number.isNaN(t.end));
  if (!spanTimes.length) {
    return 0;
  }
  const start = Math.min(...spanTimes.map((t) => t.start));
  const end = Math.max(...spanTimes.map((t) => t.end));
  return (end - start) / 1000;
};

export const traceGetStartTime = (trace: Trace): string => {
  if (!trace.spans.length) {
    return trace.created_at;
  }
  const startTimes = trace.spans
    .map((span) => new Date(span.start_time).getTime())
    .filter((time) => !Number.isNaN(time));
  if (!startTimes.length) {
    return trace.created_at;
  }
  return new Date(Math.min(...startTimes)).toISOString();
};

export const traceGetTotalTokens = (trace: Trace): number | undefined => {
  if (!trace?.spans?.length) return undefined;

  const totals = trace.spans
    .map((span) => spanGetUsage(span)?.total_tokens)
    .filter((t): t is number => typeof t === "number");

  if (!totals.length) return undefined;

  return totals.reduce((sum, t) => sum + t, 0);
};

export const TRACE_STATUS_PRIORITY = [
  "failed",
  "needs_review",
  "running",
  "completed",
];
