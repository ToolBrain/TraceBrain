export interface Span {
  span_id: string;
  parent_id: string | null;
  name: string;
  start_time: string;
  end_time: string;
  attributes: Record<string, any>;
}

export interface Feedback {
  rating?: number;
  comment?: string;
  tags?: string[];
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface Trace {
  trace_id: string;
  created_at: string;
  feedbacks: Feedback[];
  attributes: Record<string, any>;
  spans: Span[];
}

export interface Episode {
  episode_id: string;
  traces: Trace[];
}
