import type { Trace } from "../../types/trace";

export interface EpisodeList {
  total: number;
  skip: number;
  limit: number;
  episodes: { episode_id: string; traces: Trace[] }[];
}

export interface TraceFilters {
  status: string;
  errorType: string;
  minRating: number | null;
  minConfidence: number | null;
  maxConfidence: number | null;
  startTime: string;
  endTime: string;
}

export interface EpisodeFilters {
  minConfidenceLt: number | null;
}