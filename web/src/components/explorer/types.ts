import type { Trace } from "../../types/trace";

export interface EpisodeList {
  total: number;
  skip: number;
  limit: number;
  episodes: { episode_id: string; traces: Trace[] }[];
}