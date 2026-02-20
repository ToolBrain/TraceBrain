import React, { useEffect, useState } from "react";
import TraceVisualizer from "../components/trace/TraceVisualizer";
import {
  fetchEpisodeTraces,
  fetchTrace,
  addHistory,
} from "../components/utils/api";
import type { Trace } from "../types/trace";
import { useParams, useSearchParams } from "react-router-dom";
import { traceGetEvaluation } from "../components/utils/traceUtils";

const TracePage: React.FC = () => {
  const [traces, setTraces] = useState<Trace[]>([]);
  const { id } = useParams<{ id: string }>() as { id: string };
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type"); // trace or episode

  // Fetch episode or trace depending on type passed in
  useEffect(() => {
    const historyType = type === "episode" ? "episode" : "trace";

    // Record history
    addHistory(id, historyType);

    let isActive = true;
    let pollId: number | null = null;

    const loadTrace = async () => {
      if (type === "episode") {
        const episodeTraces = await fetchEpisodeTraces(id);
        if (isActive) setTraces(episodeTraces);
        return;
      }

      const traceData = await fetchTrace(id);
      if (!isActive) return;
      setTraces(traceData);

      const evaluation = traceGetEvaluation(traceData[0]);
      if (!evaluation && pollId === null) {
        pollId = window.setInterval(async () => {
          const refreshed = await fetchTrace(id);
          if (!isActive) return;
          setTraces(refreshed);
          const evalNow = traceGetEvaluation(refreshed[0]);
          if (evalNow && pollId !== null) {
            window.clearInterval(pollId);
            pollId = null;
          }
        }, 4000);
      }
    };

    loadTrace();

    return () => {
      isActive = false;
      if (pollId !== null) {
        window.clearInterval(pollId);
      }
    };
  }, [id, type]);

  return <TraceVisualizer traces={traces} />;
};

export default TracePage;
