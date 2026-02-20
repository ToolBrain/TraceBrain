import type { Trace } from "../../types/trace";

export interface HistoryList {
  type: string;
  data: Trace[] | Record<string, Trace[]>;
  has_more: boolean;
  total: number;
  limit: number;
  offset: number;
}
