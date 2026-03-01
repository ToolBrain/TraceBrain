import type { Episode } from "../../types/trace";
import type { ChipStatus } from "../shared/StatusChip";
import {
  TRACE_STATUS_PRIORITY,
  traceGetConfidence,
  traceGetDuration,
  traceGetPriority,
  traceGetStartTime,
  traceGetStatus,
  traceGetTotalTokens,
} from "./traceUtils";

export function episodeGetPriority(episode: Episode) {
  const priorities = episode.traces
    .map((trace) => traceGetPriority(trace))
    .filter((p): p is number => typeof p === "number");

  return Math.round(
    priorities.reduce((sum, p) => sum + p, 0) / priorities.length,
  );
}

export const episodeGetStartTime = (episode: Episode): string => {
  const startTimes = episode.traces
    .map((trace) => traceGetStartTime(trace))
    .filter(Boolean)
    .map((t) => new Date(t).getTime());

  return new Date(Math.min(...startTimes)).toISOString();
};

export const episodeGetTotalTokens = (episode: Episode): number | undefined => {
  const totals = episode.traces
    .map((trace) => traceGetTotalTokens(trace))
    .filter((t): t is number => typeof t === "number");

  if (!totals.length) return undefined;

  return totals.reduce((sum, t) => sum + t, 0);
};

export const episodeGetDuration = (episode: Episode): number => {
  const durations = episode.traces.map((trace) => traceGetDuration(trace));
  return durations.reduce((sum, d) => sum + d, 0);
};

export function episodeGetStatus(episode: Episode): ChipStatus {
  const traceStatuses = episode.traces.map((trace) => traceGetStatus(trace));

  for (const status of TRACE_STATUS_PRIORITY) {
    if (traceStatuses.includes(status)) return status as ChipStatus;
  }

  return "running";
}

export function episodeGetAverageConfidence(episode: Episode): number | undefined {
  const confidences = episode.traces
    .map((trace) => traceGetConfidence(trace))
    .filter((c): c is number => c !== undefined);

  if (confidences.length === 0) return undefined;

  return confidences.reduce((sum, c) => sum + c, 0) / confidences.length;
}