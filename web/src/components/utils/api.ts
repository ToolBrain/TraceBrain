import type { Trace } from "../../types/trace";

export const fetchTraces = async (
  skip?: number,
  limit?: number,
): Promise<Trace[]> => {
  const params = new URLSearchParams();
  if (skip !== undefined) params.append("skip", String(skip));
  if (limit !== undefined) params.append("limit", String(limit));

  const url = `/api/traces?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok)
    throw new Error(`Failed to fetch traces: ${response.status}`);

  const data = await response.json();
  return data.traces;
};

export const fetchTrace = async (id: string): Promise<Trace[]> => {
  try {
    const response = await fetch(`/api/traces/${id}`);
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
    const response = await fetch(`/api/episodes/${id}/traces`);
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

    const response = await fetch(`/api/traces/${id}/feedback`, {
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
  const response = await fetch(`/api/ai_evaluate/${id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      judge_model_id: judgeModelId,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to evaluate trace");
  }

  return response.json();
};

export const fetchEpisodes = async () => {};
