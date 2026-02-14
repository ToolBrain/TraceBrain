export interface Span {
  span_id: string;
  parent_id: string | null;
  name: string;
  start_time: string;
  end_time: string;
  attributes: Record<string, any>;
}

export interface Trace {
  trace_id: string;
  created_at: string;
  feedbacks: any[];
  attributes: Record<string, any>;
  spans: Span[];
}

export interface Episode {
  episode_id: string;
  traces: Trace[];
}
