import React, { useEffect, useState } from "react";
import TraceVisualizer from "../components/trace/TraceVisualizer";
import { fetchEpisodeTraces, fetchTrace } from "../components/utils/api";
import type { Trace } from "../types/trace";
import { useParams, useSearchParams } from "react-router-dom";

const TracePage: React.FC = () => {
  const [traces, setTraces] = useState<Trace[]>([]);
  const { id } = useParams<{ id: string }>() as { id: string };
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type"); // trace or episode

  // Fetch episode or trace depending on type passed in
  useEffect(() => {
    if (type === "episode") {
      fetchEpisodeTraces(id).then(setTraces);
    } else {
      fetchTrace(id).then(setTraces);
    }
  }, []);

  return <TraceVisualizer traces={traces} />;
};

export default TracePage;
