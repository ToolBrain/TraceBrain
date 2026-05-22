import React, { useEffect } from "react";
import TraceExplorer from "../components/trace-explorer/TraceExplorer";
import { fetchEpisodeTraces, fetchTrace, addHistory } from "../components/utils/api";
import { useParams, useSearchParams } from "react-router-dom";
import { traceGetEvaluation } from "../components/utils/traceUtils";
import { useQuery } from "@tanstack/react-query";

const TraceExplorerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>() as { id: string };
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type"); // trace or episode

  // Fetch episode or trace depending on type passed in
  useEffect(() => {
    const historyType = type === "episode" ? "episode" : "trace";

    // Record history
    addHistory(id, historyType);
  }, [id, type]);

  useQuery({
    queryKey: ["traces", type, id],
    queryFn: () =>
      type === "episode" ? fetchEpisodeTraces(id) : fetchTrace(id),
    refetchInterval: (query) => {
      if (type === "episode") return false;
      const data = query.state.data as Awaited<ReturnType<typeof fetchTrace>> | undefined;
      if (!data) return false;
      const evaluation = traceGetEvaluation(data[0]);
      return evaluation ? false : 4000;
    },
  });

  return <TraceExplorer />;
};

export default TraceExplorerPage;
