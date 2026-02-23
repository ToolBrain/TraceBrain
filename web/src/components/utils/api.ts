import type { Trace } from "../../types/trace";
import type { EpisodeList } from "../explorer/types";
import type { HistoryList } from "../history/types";
import type { CurriculumTask } from "../roadmap/types";

export const fetchTraces = async (
  skip?: number,
  limit?: number,
  query?: string,
): Promise<{ traces: Trace[]; total: number; skip: number; limit: number }> => {
  const params = new URLSearchParams();
  if (skip !== undefined) params.append("skip", String(skip));
  if (limit !== undefined) params.append("limit", String(limit));
  if (query) params.append("query", query);

  const response = await fetch(`/api/v1/traces?${params.toString()}`);
  if (!response.ok)
    throw new Error(`Failed to fetch traces: ${response.status}`);

  return await response.json();
};

export const fetchTrace = async (id: string): Promise<Trace[]> => {
  try {
    const response = await fetch(`/api/v1/traces/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch trace: ${response.status}`);
    }
    const trace: Trace = await response.json();
    return [trace];
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const fetchEpisodeTraces = async (id: string): Promise<Trace[]> => {
  try {
    const response = await fetch(`/api/v1/episodes/${id}/traces`);
    if (!response.ok) {
      throw new Error(`Failed to fetch episode traces: ${response.status}`);
    }
    const data: { episode_id: string; traces: Trace[] } = await response.json();
    return data.traces;
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const fetchEpisodes = async (
  skip: number = 0,
  limit: number = 10,
  query?: string,
): Promise<EpisodeList> => {
  const params = new URLSearchParams();
  params.append("skip", String(skip));
  params.append("limit", String(limit));
  if (query) params.append("query", query);

  try {
    const response = await fetch(`/api/v1/episodes?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch episodes: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const submitTraceFeedback = async (
  id: string,
  rating: number,
  comment: string,
  tags?: string[],
  metadata?: Record<string, any>,
): Promise<void> => {
  try {
    const body = { rating, comment } as Record<string, any>;
    if (tags) body.tags = tags;
    if (metadata) body.metadata = metadata;

    const response = await fetch(`/api/v1/traces/${id}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit feedback: ${response.status}`);
    }
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const evaluateTrace = async (id: string, judgeModelId: string) => {
  const response = await fetch(`/api/v1/ai_evaluate/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      judge_model_id: judgeModelId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail);
  }

  return response.json();
};

export const generateCurriculum = async (params: {
  error_types: string[] | null;
  limit: number;
}): Promise<{
  status: string;
  tasks_generated: number;
}> => {
  const response = await fetch("/api/v1/curriculum/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok)
    throw new Error(`Failed to generate curriculum: ${response.status}`);
  return response.json();
};

export const fetchCurriculumTasks = async (): Promise<CurriculumTask[]> => {
  const response = await fetch("/api/v1/curriculum");
  if (!response.ok)
    throw new Error(`Failed to fetch curriculum tasks: ${response.status}`);
  return response.json();
};

export const fetchExportCurriculum = async (
  format: "json" | "jsonl" = "json",
): Promise<any> => {
  const params = new URLSearchParams({ format });
  const response = await fetch(
    `/api/v1/curriculum/export?${params.toString()}`,
  );
  if (!response.ok)
    throw new Error(`Failed to export curriculum: ${response.status}`);

  if (format === "jsonl") {
    return response.text();
  }

  return response.json();
};

export const signalTraceIssue = async (traceId: string, reason: string) => {
  try {
    const response = await fetch(`/api/v1/traces/${traceId}/signal`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to signal trace");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    throw error;
  }
};

export const fetchHistory = async (
  limit: number,
  offset: number,
  type: "trace" | "episode",
  query?: string,
): Promise<HistoryList> => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    type,
  });

  if (query) params.set("query", query);

  const response = await fetch(`/api/v1/history?${params.toString()}`);
  if (!response.ok)
    throw new Error(`Failed to fetch history: ${response.status}`);

  return response.json();
};

export const addHistory = async (
  id: string,
  type: "trace" | "episode",
): Promise<void> => {
  try {
    const response = await fetch("/api/v1/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, type }),
    });

    if (!response.ok) {
      return;
    }

    await response.json();
  } catch {}
};

export const clearHistory = async (): Promise<void> => {
  try {
    const response = await fetch("/api/v1/history", {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to clear history: ${response.status}`);
    }
  } catch (error) {
    console.error(error);
    throw error;
  }
};

export const batchEvaluateTraces = async () => {
  try {
    const response = await fetch(`/api/v1/ops/batch_evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to batch evaluate traces");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    throw error;
  }
};
